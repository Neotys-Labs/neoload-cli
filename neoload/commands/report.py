import click
import jinja2
import json
import os
import webbrowser
import re
import statistics
import math
import time

from neoload_cli_lib import tools, rest_crud, user_data, displayer
from neoload_cli_lib.name_resolver import Resolver
from dateutil.relativedelta import relativedelta

import logging
import concurrent.futures
import requests

requests.adapters.DEFAULT_RETRIES = 5
MAX_RESULTS_WORKERS = 2
MAX_ELEMENTS_WORKERS = 10

__endpoint = "/test-results"
__operation_statistics = "/statistics"
__operation_sla_global = "/slas/statistics"
__operation_sla_test = "/slas/per-test"
__operation_sla_interval = "/slas/per-interval"
__operation_results_raw = "/raw"

__operation_events = "/events"
__operation_elements = "/elements"
__operation_monitors = "/monitors"

QUERY_CATEGORY_TRANSACTION = "category=TRANSACTION"

__resolver = Resolver(__endpoint, rest_crud.base_endpoint_with_workspace)

meta_key = 'result id'
gprint = print

@click.command()
@click.option('--template', help="A built-in known report type or the file path to the .j2 template. Built-in types include:    'builtin:transactions-csv'     'builtin:transactions-json'")
@click.option('--json-in', help="The file path to the .json data if previously stored using --out-file and no template or a json template")
@click.option('--out-file', help="The file path to the resulting output, or none to print to stdout")
@click.option('--filter', help="A filter statement to scope to a timespan and/or specify which reports and elements to use for multi-result analysis")
@click.option('--type', 'report_type',
                type=click.Choice(['single','trends'], case_sensitive=False),
                required=False, default="single",
                help="Specify which type of JSON data document to compile (default is 'single')")
@click.argument("name", type=str, required=False)
def cli(template, json_in, out_file, filter, report_type, name):
    """Generate builtin or custom Jinja reports based on test results data
    Example: neoload report --template builtin:transactions-csv
    See more templates, examples, filters with "neoload report"
    """

    if all(v is None for v in [template,json_in,out_file,filter]):
        print_extended_help()
        tools.system_exit({'code':1,'message':''})
        return

    global gprint

    model = initialize_model(filter, template)

    logger = logging.getLogger()

    # if intent is to produce JSON directly to stdout, hide print statements
    if out_file is None: gprint = lambda msg: logger.info(msg)

    json_data = parse_source_data_spec(json_in, model, report_type, name)

    json_data['cli'] = {
        'arguments': {
            'template': template,
            'json_in': json_in,
            'out_file': out_file,
            'filter': filter,
            'report_type': report_type,
            'name': name
        },
        'debug': logging.getLogger().level == logging.DEBUG,
        'internals': {
            'version': tools.compute_version()
        }
    }

    final_output = process_final_output(template, model.get("template_text"), json_data)

    if tools.__is_color_terminal():
        final_output = displayer.colorize_text(final_output)

    if out_file is not None:
        set_file_text(out_file, final_output)

        if tools.is_user_interactive() and (out_file.lower().endswith(".html") or out_file.lower().endswith(".htm")):
            webbrowser.open_new_tab("file://" + out_file)

    else:
        print(final_output)


def initialize_model(filter, template):
    filter_spec = parse_filter_spec(filter)

    if 'include_filter' in filter_spec and filter_spec['include_filter'] is not None:
        components = get_default_components(False,filter_spec['include_filter'])
    else:
        components = get_default_components(True,filter_spec['exclude_filter'])

    logging.debug(components)

    model = {
        "filter_spec": filter_spec,
        "components": components
    }

    # process template, if specified
    if template and template.strip():
        parse_template_spec(model,filter_spec,template.strip())

    return model


def parse_filter_spec(filter_spec):

    ret = {}
    ret['time_filter'] = None
    ret['results_filter'] = None
    ret['elements_filter'] = None
    ret['exclude_filter'] = None
    ret['include_filter'] = None

    if filter_spec is not None:
        filter_parts = filter_spec.split(";")
        for s in filter_parts:
            if s.startswith("timespan"):
                ret['time_filter'] = s.replace("timespan=","",1)
            elif s.startswith("results"):
                ret['results_filter'] = s.replace("results=","",1)
            elif s.startswith("elements"):
                ret['elements_filter'] = s.replace("elements=","",1)
            elif s.startswith("exclude"):
                ret['exclude_filter'] = s.replace("exclude=","",1)
            elif s.startswith("include"):
                ret['include_filter'] = s.replace("include=","",1)

    return ret

def parse_template_spec(model,filter_spec,template):
    if template.lower().startswith("builtin:transactions"):
        model["components"] = get_default_components(False,filter_spec["exclude_filter"])
        model["components"]["transactions"] = True
        if template.lower().endswith("-csv"):
            model["template_text"] = get_builtin_template_transaction_csv()

    elif template.lower().startswith("builtin:console-summary"):
        model["components"] = get_default_components(False,filter_spec["exclude_filter"])
        model["components"]["transactions"] = True
        model["components"]["summary"] = True
        model["components"]["statistics"] = True
        model["components"]["slas"] = True
        model["template_text"] = get_builtin_console_summary()

    elif os.path.isfile(template):
        model["template_text"] = get_file_text(template)
    else:
        tools.system_exit({'message': "template value is not a file or a known type", 'code': 2})


def parse_source_data_spec(json_in, model, report_type, name):
    filter_spec = model['filter_spec']

    if json_in is not None:
        return json.loads(get_file_text(json_in))

    # no in file, so go out to source live
    if report_type == "single":
        return get_single_report(name,model["components"],filter_spec["time_filter"],filter_spec["elements_filter"],filter_spec["exclude_filter"])
    elif report_type == "trends":
        return get_trends_report(name,filter_spec["time_filter"],filter_spec["results_filter"],filter_spec["elements_filter"],filter_spec["exclude_filter"])
    else:
        tools.system_exit({'message': "No report_type named '" + report_type + "'.", 'code': 2})


def process_final_output(template, template_text, json_data):
    if template_text is None or template_text == "":
        return json.dumps(json_data)
    else:
        dirname = os.path.dirname(os.path.abspath(template))
        loader = jinja2.FileSystemLoader(searchpath=dirname)
        env = jinja2.Environment(loader=loader,autoescape=True,extensions=['jinja2.ext.debug'])
        t = env.from_string(template_text)

        return t.render(json_data)


def add_component_if(components,key,default,component_list):
    components[key] = default if not key in components else components[key]
    if component_list is not None and key in component_list.split(","):
        components[key] = not default

def get_default_components(default_retrieve=True,component_list=None):
    components = {}
    add_if = lambda key, default: add_component_if(components,key,default,component_list)
    add_if('summary',True) # always get summary, because many other components depend on summary elements
    add_if('statistics',default_retrieve)
    add_if('slas',default_retrieve)
    add_if('events',default_retrieve)
    add_if('transactions',default_retrieve)
    add_if('all_requests',default_retrieve)
    add_if('ext_data',default_retrieve)
    add_if('monitors',default_retrieve)
    add_if('controller_points',default_retrieve)
    return components

def can_raw_transactions_data():
    return False if user_data.is_version_lower_than('2.6.0') else True

def should_raw_transactions_data(__id, time_filter):
    if time_filter is None:
        return False

    use_raw = can_raw_transactions_data()
    logging.debug("use_raw[0]: " + str(use_raw))
    if use_raw:
        # look for the transaction with the smallest number of iterations, but that has raw data

        # grab all transactions list
        json_elements_transactions = rest_crud.get(get_end_point(__id, __operation_elements) + "?" + QUERY_CATEGORY_TRANSACTION)
        txns = []
        for el in json_elements_transactions:
            if el['id'] == 'TRANSACTION':
                # grab count of this transaction and only add if there are iterations
                json_values = rest_crud.get(get_end_point(__id, __operation_elements) + "/" + el['id'] + "/values")
                if json_values['count'] > 0:
                    txns.append({
                        'id': el['id'],
                        'count': json_values['count']
                    })

        raw_sum = 0

        # sort ascending by count (smallest number of iterations produces smallest amount of data)
        txns = sorted(txns, key=lambda el: el['count'])
        for el in txns:
            this_raw_count = len(rest_crud.get(get_end_point(__id, __operation_elements) + "/" + el['id'] + "/raw?format=JSON"))
            raw_sum += this_raw_count
            if raw_sum > 0:
                break

        if raw_sum < 1:
            use_raw = False
            logging.debug("use_raw[1]: " + str(use_raw))
    return use_raw

def parse_to_id(name_or_id):
    val = name_or_id
    if val == "cur":
        val = user_data.get_meta(meta_key)
    is_id = tools.is_id(val)

    __id = tools.get_id(val, __resolver, is_id)

    if not __id:
        __id = user_data.get_meta_required(meta_key)

    return __id

def get_single_report(name,components=None,time_filter=None,elements_filter=None,exclude_filter=None):

    if components is None: components = get_default_components(True,exclude_filter)

    __id = parse_to_id(name)

    data = {
        'id': __id,
        'summary': {},#json_result,
        'statistics': {},#json_stats,
        'sla_global': [],#json_sla_global,
        'sla_test': [],#json_sla_test,
        'sla_interval': [],#json_sla_interval,
        'events': [],#json_events,
        'elements': {
            'transactions': [],#json_elements_transactions
        },
        'all_requests': [],#json_elements_all_requests[0] if json_elements_all_requests is not None else {},
        'ext_data': [],#ext_datas,
        'controller_points': [],#ctrl_datas,
        'monitors': []
    }

    time_binding = None
    if time_filter is not None:
        time_binding = {
            "time_filter": time_filter
        }

    time_binding = fill_single_summary(__id, time_binding, time_filter, components, data)

    fill_single_slas(__id, components, data)

    fill_single_stats(__id, components, data)

    fill_single_events(__id, components, data)

    statistics_list = get_standard_statistics_list()

    use_txn_raw = should_raw_transactions_data(__id, time_filter)

    fill_single_requests(__id, elements_filter, time_binding, statistics_list, use_txn_raw, components, data)

    fill_single_transactions(__id, elements_filter, time_binding, statistics_list, use_txn_raw, components, data)

    fill_single_monitors(__id, components, data)

    fill_single_ext_data(__id, components, data)

    fill_single_controller_points(__id, components, data)

    return data

def get_standard_statistics_list():
    return ["AVG_DURATION","MIN_DURATION","MAX_DURATION","COUNT","THROUGHPUT",
                "ELEMENTS_PER_SECOND","ERRORS","ERRORS_PER_SECOND","ERROR_RATE",
                "AVG_TTFB","MIN_TTFB","MAX_TTFB"]


def fill_single_summary(__id, time_binding, time_filter, components, data):
    if components['summary'] or components['slas'] or time_filter is not None:
        gprint("Getting test results...")
        json_result = rest_crud.get(get_end_point(__id))
        json_result = add_test_result_summary_fields(json_result)
        data['summary'] = json_result
        if time_binding is not None:
            time_binding["summary"] = json_result
            time_binding = fill_time_binding(time_binding)
    return time_binding

def summary_precludes_details_fetch(data):
    return data['summary']['terminationReason'] in ['LG_AVAILABILITY', 'FAILED_TO_START','UNKNOWN']

def fill_single_slas(__id, components, data):
    if summary_precludes_details_fetch(data): return
    if components['slas']:
        status = data['summary']['status']
        gprint("Getting global SLAs...")
        data['sla_global'] = [] if status!='TERMINATED' else rest_crud.get(get_end_point(__id, __operation_sla_global))
        gprint("Getting per-test SLAs...")
        data['sla_test'] = [] if status!='TERMINATED' else rest_crud.get(get_end_point(__id, __operation_sla_test))
        gprint("Getting per-interval SLAs...")
        data['sla_interval'] = rest_crud.get(get_end_point(__id, __operation_sla_interval))

def fill_single_stats(__id, components, data):
    if summary_precludes_details_fetch(data): return
    if components['statistics']:
        gprint("Getting test statistics...")
        data['statistics'] = rest_crud.get(get_end_point(__id, __operation_statistics))

def fill_single_events(__id, components, data):
    if summary_precludes_details_fetch(data): return
    if components['events']:
        gprint("Getting events...")
        data['events'] = rest_crud.get(get_end_point(__id, __operation_events))

def fill_single_requests(__id, elements_filter, time_binding, statistics_list, use_txn_raw, components, data):
    if summary_precludes_details_fetch(data): return
    if components['all_requests']:
        gprint("Getting all-request data...")

        json_elements_requests = rest_crud.get(get_end_point(__id, __operation_elements) + "?category=REQUEST")
        json_elements_all_requests = list(filter(lambda m: m['id'] == 'all-requests', json_elements_requests))
        json_elements_all_requests_preserve = json_elements_all_requests

        if not elements_filter is None:
            json_elements_all_requests = filter_elements(json_elements_all_requests, elements_filter)

        if not any(filter(lambda m: m['id'] == 'all-requests', json_elements_all_requests)):
            json_elements_all_requests = json_elements_all_requests + json_elements_all_requests_preserve

        json_elements_all_requests = get_elements_data(__id, json_elements_all_requests, time_binding, True, statistics_list, use_txn_raw)

        data['all_requests'] = json_elements_all_requests[0] if json_elements_all_requests is not None and len(json_elements_all_requests) > 0 else {},

def fill_single_transactions(__id, elements_filter, time_binding, statistics_list, use_txn_raw, components, data):
    if summary_precludes_details_fetch(data): return
    if components['transactions']:
        gprint("Getting transactions...")

        json_elements_transactions = rest_crud.get(get_end_point(__id, __operation_elements) + "?" + QUERY_CATEGORY_TRANSACTION)
        if not elements_filter is None:
            json_elements_transactions = filter_elements(json_elements_transactions, elements_filter)

        json_elements_transactions = get_elements_data(__id, json_elements_transactions, time_binding, True, statistics_list, use_txn_raw)
        json_elements_transactions = list(sorted(json_elements_transactions, key=lambda x: x['display_name']))

        data['elements']['transactions'] = json_elements_transactions

def fill_single_monitors(__id, components, data):
    if summary_precludes_details_fetch(data): return
    if components['monitors'] or components['controller_points'] or components['ext_data']:
        gprint("Getting monitors...")
        filled = rest_crud.get(get_end_point(__id, __operation_monitors))
        filled = get_mon_datas(__id, lambda m: True, filled, True)
        filled = list(sorted(filled, key=lambda x: x['display_name']))
        data['monitors'] = filled

def fill_single_ext_data(__id, components, data):
    if summary_precludes_details_fetch(data): return
    if components['ext_data']:
        ext_datas = get_mon_datas(__id, lambda m: m['path'][0] == 'Ext. Data', data['monitors'], True)
        ext_datas = list(sorted(ext_datas, key=lambda x: x['display_name']))
        data['ext_data'] = ext_datas

def fill_single_controller_points(__id, components, data):
    if summary_precludes_details_fetch(data): return
    if components['controller_points']:
        data['controller_points'] = get_mon_datas(__id, lambda m: m['path'][0] == 'Controller', data['monitors'], True)

# examples
# --filter "timespan=2m-4m"
# --filter "timespan=10%-90%"
# --filter "timespan=5m15s;results=cur|-2;elements=11a783ad-ae93-4f05-8517-3fd2feb8452d|S05_Checkout|(.*)Login"
def fill_time_binding(time_binding):
    try:
        timespan_spec = time_binding["time_filter"] if "time_filter" in time_binding else None
        if not timespan_spec is None:
            total_duration_sec = time_binding["summary"]["duration"] / 1000
            time_parts = timespan_spec.split("-")
            from_spec = time_parts[0] if len(time_parts[0].strip())>0 else None
            to_spec = time_parts[1] if len(time_parts) > 1 and len(time_parts[1].strip())>0 else None
            from_secs = 0 if from_spec is None else translate_time_part_to_seconds(total_duration_sec, from_spec)
            to_secs = total_duration_sec if to_spec is None else translate_time_part_to_seconds(total_duration_sec, to_spec)
            time_binding['from_secs'] = round(from_secs)
            time_binding['to_secs'] = round(to_secs)
        return time_binding
    except Exception:
        raise ValueError("Something went wrong while fill_time_binding")


def translate_time_part_to_seconds(total_duration_sec, part_spec):
    time_part_mod_to_sec = {
        "h": lambda x: x * 60 * 60,
        "m": lambda x: x * 60,
        "s": lambda x: x
    }
    try:
        if part_spec.endswith("%"):
            return (int(part_spec.replace("%","")) / 100.0) * total_duration_sec
        else:
            secs = 0
            final_spec = part_spec.strip()

            for key in time_part_mod_to_sec:
                arr = final_spec.split(key)
                if arr[0].isdigit():
                    secs += time_part_mod_to_sec[key](int(arr[0]))
                    final_spec = final_spec.replace(arr[0]+key,"",1)

            if len(final_spec) > 0:
                raise ValueError("Characters left over in timespan part spec, invalid: '" + final_spec + "'")

            return secs

    except Exception:
        raise ValueError("Value of filter timespan part '" + part_spec + "' is invalid.")

def get_trends_report(name, time_filter, results_filter, elements_filter, exclude_filter):
    (arr_ids,arr_directives) = parse_results_filter(results_filter)

    (count_back,count_ahead) = get_trend_count_back_ahead(arr_directives)

    if len(arr_ids) < 1:
        arr_ids.append({
            "id": parse_to_id(name),
            "type": "result"
        })

    if len(arr_ids) < 1:
        raise ValueError("Trend requires 1 or more results in the filter!")

    arr_selected = get_trends_selected_results(arr_ids,count_back,count_ahead)

    all_transactions = []

    fill_trend_results(arr_selected, all_transactions, elements_filter, time_filter)

    all_transaction_names = list(map(lambda t: t["name"], all_transactions))
    unique_transaction_names = unique(all_transaction_names)

    unique_transactions = []
    transaction_aggregates = ["avgDuration","elementPerSecond","percentile50","percentile90","percentile95","percentile99"]
    for name in unique_transaction_names:
        fill_trend_transaction_group(name,transaction_aggregates,arr_selected,unique_transactions)

    return {
        "summary": {
            "title": "Comparison"
        },
        "unique_transactions": unique_transactions,
        "results": arr_selected,
    }

def fill_trend_results(arr_selected, all_transactions, elements_filter, time_filter):

    procedure = lambda result: fill_trend_result(result, all_transactions, elements_filter, time_filter)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_RESULTS_WORKERS) as executor:
        translate = {executor.submit(procedure, result): result for result in arr_selected}
        for future in concurrent.futures.as_completed(translate):
            i = translate[future]
            elapsed = 0
            try:
                start = get_perf_time()
                data = future.result()
                elapsed = get_perf_time() - start
            except Exception as exc:
                logging.error('%r generated an exception: %s' % (i, exc))
            else:
                logging.getLogger().info("parallel processed fill_trend_results worker for '{}' in {} seconds".format(data['name'],perf_time_to_sec(elapsed)))

    return arr_selected

def parse_results_filter(results_filter):
    filter_parts = results_filter.split("|") if results_filter is not None else []
    arr_ids = []
    arr_directives = []
    for part in filter_parts:
        if is_guid(part):
            arr_ids.append({
                "id": part,
                "type": "result"
            })
        elif part == "cur":
            arr_ids.append({
                "id": parse_to_id("cur"),
                "type": "result"
            })
        else:
            arr_directives.append(part)

    return (arr_ids,arr_directives)

def get_trend_count_back_ahead(arr_directives):
    count_back = 0 # negative
    count_ahead = 0 # positive
    for d in arr_directives:
        if d.startswith("+") and is_integer(d):
            count_ahead = int(d)
        elif d.startswith("-") and is_integer(d):
            count_back = int(d)

    return (count_back, count_ahead)

def get_trends_selected_results(arr_ids,count_back,count_ahead):
    base_id = arr_ids[0]["id"]
    logging.debug('base_id: {}'.format(base_id))
    arr_results = get_results_by_result_id(base_id,count_back,count_ahead)
    logging.debug('selected results: {}'.format(arr_results))
    arr_sorted_by_time = list(sorted(arr_results, key=lambda x: x["startDate"]))
    base_index = list(map(lambda x: x["id"],arr_sorted_by_time)).index(base_id)
    arr_selected = []
    logging.debug('base_index: {}'.format(base_index))
    logging.debug('count_ahead: {}'.format(count_ahead))
    logging.debug('count_back: {}'.format(count_back))

    for i in range(base_index,base_index+1+count_ahead):
        arr_selected.append(arr_sorted_by_time[i])
    for i in range(base_index+count_back,base_index):
        if i > 0 and i < len(arr_sorted_by_time):
            arr_selected.append(arr_sorted_by_time[i])

    arr_selected = list(sorted(arr_selected, key=lambda x: x["startDate"]))
    for i in range(0,len(arr_selected)):
        arr_selected[i]["index"] = i

    return arr_selected

def fill_trend_result(result, all_transactions, elements_filter, time_filter):
    gprint("fill_trend_result: Getting test '" + result["name"] + "' (" + result["id"] + ") statistics...")
    __id = result["id"]
    result = add_test_result_summary_fields(result)
    json_stats = rest_crud.get(get_end_point(__id, __operation_statistics))

    statistics_list = get_standard_statistics_list()

    time_binding = None
    if time_filter is not None:
        time_binding = {
            "time_filter": time_filter
        }

    if time_binding is not None:
        time_binding["summary"] = result
        time_binding = fill_time_binding(time_binding)

    found_elements = []
    elements = []
    # elements.extend(rest_crud.get(get_end_point(__id, __operation_elements) + "?category=REQUEST"))
    transactions = rest_crud.get(get_end_point(__id, __operation_elements) + "?" + QUERY_CATEGORY_TRANSACTION)
    elements.extend(transactions)
    if elements_filter is not None and not (result['terminationReason'] in ['FAILED_TO_START']):
        filters = parse_elements_filter(elements_filter)
        logging.debug("Using filters: {}".format(filters))
        logging.debug("Filtering elements: {}".format(len(elements)))
        found_elements = filter_elements(elements, elements_filter)
        logging.debug("Filtered elements: {}".format(len(found_elements)))
    else:
        found_elements = elements

    if len(elements) > 0:
        use_txn_raw = should_raw_transactions_data(__id, time_filter)
        found_elements = get_elements_data(__id, found_elements, time_binding, True, statistics_list, use_txn_raw)
        found_elements = sorted(found_elements, key=lambda x: x["aggregate"]["avgDuration"], reverse=True)

    all_transactions.extend(list(filter(lambda el: el["type"]=="TRANSACTION", found_elements)))

    result["elements"] = found_elements
    result["statistics"] = json_stats

    return result

def fill_trend_transaction_group(name,transaction_aggregates,arr_selected,unique_transactions):
    group = {
        "name": name,
        "results": []
    }
    aggregates = {}
    for agg in transaction_aggregates:
        aggregates[agg]=[]

    for result in arr_selected:
        simplify = {
            "id": result["id"],
            "name": result["name"],
            "elements": []
        }
        els = list(filter(lambda el: el["name"] == name and el["type"] == "TRANSACTION", result["elements"]))
        simplify["elements"].extend(els)
        group["results"].append(simplify)

        for agg in transaction_aggregates:
            aggregates[agg].extend(list(map(lambda el,a=agg: el["aggregate"][a], els)))

    group["aggregate"] = {}
    for agg in transaction_aggregates:
        group["aggregate"]["max_"+agg]=max(aggregates[agg])

    unique_transactions.append(group)

def add_test_result_summary_fields(json_result):
    json_result["startDateText"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(json_result['startDate']/1000))
    json_result["endDateText"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(json_result['endDate']/1000))
    json_result["durationText"] = ", ".join(get_human_readable_time(relativedelta(seconds=((json_result['endDate']-json_result['startDate'])/1000))))
    return json_result

def is_integer(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def is_guid(s):
    return re.search(r"(\{){0,1}[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}(\}){0,1}", s)

def filter_elements(elements, elements_filter):
    found = []
    if elements_filter is not None:
        filters = parse_elements_filter(elements_filter)
        for fil in filters:
            if fil["type"] == "id":
                found.extend(list(filter(lambda el,f=fil: el["id"] == f["value"], elements)))
            elif fil["type"] == "regex":
                found.extend(list(filter(lambda el,f=fil: element_matches_regex(el, f["value"]), elements)))
            else:
                raise ValueError
    return found

def parse_elements_filter(elements_filter):
    filters = list(map(lambda s: {
        "type": "id" if is_guid(s) else "regex",
        "value": s if is_guid(s) else re.compile(s),
    }, elements_filter.split("|")))
    return filters

def element_matches_regex(element, pattern):
    strs = [element["id"], element["name"]]
    if 'path' in element:
        strs.append(get_element_parent(element))
        strs.append(get_element_user_path(element))
    return any(filter(lambda s: False if s is None or s=="" else bool(pattern.search(s)), strs))

def get_element_parent(el):
    return el['path'][-2] if 'path' in el and len(el['path'])>1 else "" # name of element is always last, parent is one before last

def get_element_user_path(el):
    return el['path'][0] if 'path' in el and len(el['path'])>0 else ""

def get_results_by_result_id(__id,count_back,count_ahead):
    result = rest_crud.get(get_end_point(__id))
    project = result["project"]
    scenario = result["scenario"]
    logging.debug({'project':project,'scenario':scenario})
    total_expected = -count_back + 1 + count_ahead
    results = []
    logging.debug("based_id: {}".format(__id))
    logging.debug("total_expected: {}".format(total_expected))
    logging.debug("count_back: {}".format(count_back))
    logging.debug("count_ahead: {}".format(count_ahead))

    page_size = 200
    params = {
        'limit': page_size,
        'offset': 0,
        'sort': '-startDate',
        'project': project
    }

    # Get first page
    all_entities = []
    # Get all other pages
    while len(results) < total_expected:
        entities = rest_crud.get(get_versioned_endpoint_base(), params)
        ret_count = len(entities)
        # Exit the loop when the pagination is not implemented for the endpoint and the number of entities is equal to page_size
        if ret_count == 0:
            break

        entities = list(filter(lambda el: el['scenario'] == scenario, entities))

        all_entities += entities
        params['offset'] += page_size

        arr_sorted_by_time = list(sorted(all_entities, key=lambda x: x["startDate"]))

        results = compile_results_from_source(__id, arr_sorted_by_time, count_back, count_ahead)

        if ret_count < page_size:
            break

    return results

def compile_results_from_source(base_id, all_entities, count_back, count_ahead):
    ret = []
    if len(list(filter(lambda x: x['id'] == base_id, all_entities))) > 0:
        base_index = list(map(lambda x: x["id"],all_entities)).index(base_id)
        back_index = base_index+count_back
        ahead_index = base_index+count_ahead
        #print({'base_index':base_index,'back_index':back_index,'ahead_index':ahead_index})
        for i in range(max(back_index,0),base_index+1):
            ret.append(all_entities[i])
        for i in range(base_index,min(ahead_index,len(all_entities)-1)):
            ret.append(all_entities[i])
    return ret

def get_versioned_endpoint_base():
    return rest_crud.base_endpoint_with_workspace() + __endpoint

def get_end_point(id_test: str, operation=''):
    slash_id_test = '' if id_test is None else '/' + id_test
    return get_versioned_endpoint_base() + slash_id_test + operation


def get_file_text(path):
    with open(path, 'r') as f:
        text = f.read()
    return text

def set_file_text(path,content):
    with open(path, 'w') as f:
        f.write(content)

def percentile(values, percent, key=lambda x:x):
    """
    Find the percentile of a list of values.

    @parameter N - is a list of values. Note N MUST BE already sorted.
    @parameter percent - a float value from 0.0 to 1.0.
    @parameter key - optional key function to compute value from each element of N.

    @return - the percentile of the values
    """
    if not values:
        return None
    k = (len(values)-1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return key(values[int(k)])
    d0 = key(values[int(f)]) * (c-k)
    d1 = key(values[int(c)]) * (k-f)
    return d0+d1

def get_human_readable_time(reldel):
    attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
    human_readable = lambda delta: ['%d %s' % (getattr(delta, attr), getattr(delta, attr) > 1 and attr or attr[:-1])
        for attr in attrs if getattr(delta, attr)]
    return human_readable(reldel)

def get_elements_data(result_id, base_col, time_binding, include_points, statistics_list, use_txn_raw):

    procedure = lambda el: (get_perf_time(),get_element_data(el, result_id, time_binding, include_points, statistics_list, use_txn_raw))

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_ELEMENTS_WORKERS) as executor:
        translate = {executor.submit(procedure, el): el for el in base_col}
        for future in concurrent.futures.as_completed(translate):
            orig = translate[future]
            try:
                (start,after) = future.result()
                elapsed = get_perf_time() - start
            except Exception as exc:
                logging.error('%r generated an exception: %s' % (orig, exc))
            else:
                logging.getLogger().info("parallel processed get_elements_data worker for '{}' in {} seconds".format(orig['display_name'],perf_time_to_sec(elapsed)))

    return base_col

def get_element_data(el, result_id, time_binding, include_points, statistics_list, use_txn_raw):
    full_name = get_element_full_name(el)
    parent = get_element_parent(el)
    user_path = get_element_user_path(el)
    gprint("Getting element values for '" + full_name + "'")
    json_values = rest_crud.get(get_end_point(result_id, __operation_elements) + "/" + el['id'] + "/values")

    (json_raws,json_points) = get_element_data_from_sources(include_points, time_binding, use_txn_raw, result_id, el, statistics_list)

    if len(json_raws) > 0:
        (perc_points,sum_of_count,sum_of_errors) = get_element_data_by_raws(json_raws,json_values)
    else:
        (perc_points,sum_of_count,sum_of_errors) = get_element_data_by_points(json_points,json_values)

    # from either data source, calculate common aggregates
    fill_element_data_common_values(json_values,perc_points,sum_of_count,sum_of_errors)

# {
#     "Elapsed": 38736,
#     "Time": "2020-10-05T20:58:36.487Z",
#     "User Path": "Post",
#     "Virtual User ID": "0-1",
#     "Parent": "Actions",
#     "Element": "Click Submit",
#     "Response time": 947,
#     "Success": "yes",
#     "Population": "popPost",
#     "Zone": "Default zone"
#   }
    perc_fields = list(filter(lambda x: x.startswith('percentile'), json_values.keys()))
    convert_to_seconds = ['minDuration','maxDuration','sumDuration','avgDuration'] \
                        + perc_fields

    convert_element_fields_to_seconds(convert_to_seconds,json_values)

    round_fields = convert_to_seconds \
                    + ['successRate','failureRate']

    round_element_fields(round_fields,json_values,3)

    el["display_name"] = full_name
    el["parent"] = parent
    el["user_path"] = user_path
    el["aggregate"] = json_values
    el["points"] = json_points
    el["raw"] = json_raws
    el["totalCount"] = el["aggregate"]["successCount"] + el["aggregate"]["failureCount"]
    if el["totalCount"] == 0:
        el["successRate"] = 0
        el["failureRate"] = 0
    else:
        el["successRate"] = el["aggregate"]["successCount"] / el["totalCount"]
        el["failureRate"] = el["aggregate"]["failureCount"] / el["totalCount"]

    return el

def get_element_full_name(el):
    return el['name'] if not 'path' in el else " \\ ".join(el['path'])

def get_element_data_from_sources(include_points, time_binding, use_txn_raw, result_id, el, statistics_list):
    viable_raw_element = (use_txn_raw and el['type'] in ["TRANSACTION"])
    json_raws = []
    json_points = []
    if (include_points or time_binding is not None):
        if viable_raw_element:
            logging.getLogger().debug("Starting get_element_data_from_sources for element ({})".format(el['id']))
            json_raws = rest_crud.get(get_end_point(result_id, __operation_elements) + "/" + el['id'] + "/raw?format=JSON")
        else:
            json_points = rest_crud.get(get_end_point(result_id, __operation_elements) + "/" + el['id'] + "/points?statistics=" + ",".join(statistics_list))

    if not time_binding is None:
        json_points = filter_by_time(json_points, time_binding, lambda p: int(p['from'])/1000, lambda p: int(p['to'])/1000)
        json_raws = filter_by_time(json_raws, time_binding, lambda p: p['Elapsed']/1000, lambda p: p['Elapsed']/1000)

    return (json_raws,json_points)

def get_element_data_by_raws(json_raws,json_values):
    field_name = 'Response time'
    perc_points = list(sorted(map(lambda x: x[field_name], json_raws)))
    sum_of_count = len(json_raws)
    sum_of_errors = 0 if len(json_raws) < 1 else len(list(filter(lambda x: x['Success'] not in ["yes"],json_raws)))
    json_values['minDuration'] = 0 if len(json_raws) < 1 else min(list(map(lambda x: x[field_name], json_raws)))
    json_values['maxDuration'] = 0 if len(json_raws) < 1 else max(list(map(lambda x: x[field_name], json_raws)))
    json_values['avgDuration'] = 0 if len(json_raws) < 1 else statistics.mean(list(map(lambda x: x[field_name], json_raws)))
    return (perc_points,sum_of_count,sum_of_errors)

def get_element_data_by_points(json_points,json_values):
    perc_points = list(sorted(map(lambda x: x['AVG_DURATION'], json_points)))
    sum_of_count = 0 if len(json_points) < 1 else round(sum(list(map(lambda x: x['COUNT'], json_points))),1)
    sum_of_errors = 0 if len(json_points) < 1 else round(sum(list(map(lambda x: x['ERRORS'], json_points))),1)
    json_values['minDuration'] = 0 if len(json_points) < 1 else min(list(map(lambda x: x['MIN_DURATION'], json_points)))
    json_values['maxDuration'] = 0 if len(json_points) < 1 else max(list(map(lambda x: x['MAX_DURATION'], json_points)))
    json_values['avgDuration'] = 0 if len(json_points) < 1 else statistics.mean(list(map(lambda x: x['AVG_DURATION'], json_points)))
    return (perc_points,sum_of_count,sum_of_errors)

def fill_element_data_common_values(json_values,perc_points,sum_of_count,sum_of_errors):
    json_values['count'] = round(sum_of_count, 1)
    json_values['percentile50'] = 0 if len(perc_points) < 1 else percentile(perc_points,0.5)
    json_values['percentile90'] = 0 if len(perc_points) < 1 else percentile(perc_points,0.9)
    json_values['percentile95'] = 0 if len(perc_points) < 1 else percentile(perc_points,0.95)
    json_values['percentile99'] = 0 if len(perc_points) < 1 else percentile(perc_points,0.99)
    json_values['successCount'] = sum_of_count - sum_of_errors
    json_values['successRate'] = 0 if sum_of_count == 0 else json_values['successCount'] / sum_of_count
    json_values['failureCount'] = sum_of_errors
    json_values['failureRate'] = 0 if sum_of_count == 0 else json_values['failureCount'] / sum_of_count

def convert_element_fields_to_seconds(convert_to_seconds,json_values):
    for field in convert_to_seconds:
        if field in json_values:
            if json_values[field] is None:
                raise ValueError("Field '" + field + "' is None")
            else:
                json_values[field] = json_values[field] / 1000.0

def round_element_fields(round_fields,json_values,decimal_points):
    for field in round_fields:
        if field in json_values:
            json_values[field] = round(json_values[field],decimal_points)


def filter_by_time(objs, time_binding, from_function, to_function):
    ret = []
    from_time = time_binding["from_secs"]
    to_time = time_binding["to_secs"]
    for obj in objs:
        this_from = from_function(obj)
        this_to = to_function(obj)
        if this_from >= from_time and this_to <= to_time:
            ret.append(obj)
    return ret


def get_mon_datas(result_id, l_selector, base_col, include_points):
    mons = []
    for mon in list(filter(l_selector, base_col)):
        mons.append(mon)
    for mon in mons:
        full_name = get_element_full_name(mon)
        gprint("Getting monitor values for '" + full_name + "'")
        mon_points = rest_crud.get(get_end_point(result_id, __operation_monitors) + "/" + mon['id'] + "/points")
        time_points = list(sorted(mon_points, key=lambda x: x['from']))
        perc_points = list(sorted(map(lambda x: x['AVG'], mon_points)))
        mon["display_name"] = full_name
        mon["percentiles"] = {
            'percentile50': percentile(perc_points,0.5),
            'percentile90': percentile(perc_points,0.9),
            'percentile95': percentile(perc_points,0.95),
            'percentile99': percentile(perc_points,0.99)
        }
        mon["points"] = time_points if include_points else []
    return mons

def unique(seq, idfun=None):
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

def get_builtin_template_transaction_csv():
    return """
User Path;Element;Parent;Count;Min;Avg;Max;Perc 50;Perc 90;Perc 95;Perc 99;Success;Success Rate;Failure;Failure Rate{%
    for txn in elements.transactions | rejectattr('id', 'equalto', 'all-transactions') | rejectattr('aggregate.count', 'equalto', 0) | sort(attribute='avgDuration',reverse=true) %}
{{ txn.user_path|e }};{{ txn.name|e }};{{ txn.parent|e }};{{ txn.aggregate.count }};{{ txn.aggregate.minDuration }};{{ txn.aggregate.avgDuration }};{{ txn.aggregate.maxDuration }};{{ txn.aggregate.percentile50 }};{{ txn.aggregate.percentile90 }};{{ txn.aggregate.percentile95 }};{{ txn.aggregate.percentile99 }};{{ txn.aggregate.successCount }};{{ txn.aggregate.successRate }};{{ txn.aggregate.failureCount }};{{ txn.aggregate.failureRate }}{%
    endfor %}""".strip()

def get_builtin_console_summary():
    return """

Test Name: {{summary.name}}
Start: {{summary.startDateText}}\tDuration: {{summary.durationText}}
End: {{summary.endDateText}}\tExecution Status: {{summary.status}} by {{summary.terminationReason}}
Description: {{summary.description}}
Project: {{summary.project}}
Scenario: {{summary.scenario}}
Quality Status: {{summary.qualityStatus}}

Transactions summary:
User Path\tElement\tCount\tMin\tAvg\tMax\tPerc 50\tPerc 90\tPerc 95\tPerc 99\tSuccess\tS.Rate\tFailure\tF.Rate
{% for txn in elements.transactions | rejectattr('id', 'equalto', 'all-transactions') | rejectattr('aggregate.count', 'equalto', '0') | sort(attribute='avgDuration',reverse=true)
%}{{ txn.user_path|e }}\t{{ txn.name|e }}\t{{ txn.aggregate.count }}\t""" \
"""{{ txn.aggregate.minDuration }}\t{{ txn.aggregate.avgDuration }}\t{{ txn.aggregate.maxDuration }}\t""" \
"""{{ txn.aggregate.percentile50 }}\t{{ txn.aggregate.percentile90 }}\t{{ txn.aggregate.percentile95 }}\t{{ txn.aggregate.percentile99 }}\t""" \
"""{{ txn.aggregate.successCount }}\t{{ txn.aggregate.successRate }}\t""" \
"""{{ txn.aggregate.failureCount }}\t{{ txn.aggregate.failureRate }}
{% endfor %}""".strip()


def print_extended_help():
    ctx = click.get_current_context()
    cli_help = ctx.get_help()

    print(cli_help + """


Built-in Templates:

    * builtin:transactions --> transaction aggregates in JSON format
    * builtin:transactions-csv --> transaction aggregates in CSV format
    * builtin:console-summary --> test summary and transaction aggregates in human-readable format

Filtering:

    * timespan: [from]-[to]
        * Either from or to components are optional, but not both
        * Values can be 0-100 for percentage of the total duration of test
        * Human-readable time format including #[h|m|s], such as 10m or 5m30s

    * elements:
        * a comma or semicolon separated list of element names or IDs
        * can include regex

    * results:
        * a comma or semicolon separated list of result set specifiers, such as:
            * negative (track back N number of results since current test-results)
            * positive (track forward N number of results since current test-results)
            * specific test-result IDs (for additional baselines)


Examples:

    * Print a simple list of transaction aggregates in CSV format (semicolon delimited)
        neoload report --template builtin:transactions-csv

    * Compiles and produces transaction aggregate data based on only data from a specific timespan
        neoload report --template builtin:transactions-csv --filter="timespan:10%-90%"

    * Compiles JSON data and writes to a temp file, no applying templates
        neoload report --out-file ~/temp.json

    * Uses pre-compiled JSON data file, applies a custom template, and writes output to a file
        neoload report --json-in ~/temp.json --template tests/resources/jinja/sample-custom-report.html.j2 --out-file ~/temp.html

    """)

def get_perf_time():
    logging.debug('get_perf_time: {}'.format(time.time()))
    return time.time()

def perf_time_to_sec(elapsed):
    return round(elapsed,3)
