import click
from neoload_cli_lib import tools,cli_exception
import neoload_cli_lib.schema_validation as schema_validation
import jinja2
import json
import tempfile
import os
import webbrowser
import sys
import time
import re
import statistics

import math
import functools
import datetime
import uuid

from neoload_cli_lib import tools, rest_crud, user_data, displayer, cli_exception
from neoload_cli_lib.name_resolver import Resolver

from dateutil.relativedelta import relativedelta

import logging
import concurrent.futures

__endpoint = "/test-results"
__operation_statistics = "/statistics"
__operation_sla_global = "/slas/statistics"
__operation_sla_test = "/slas/per-test"
__operation_sla_interval = "/slas/per-interval"

__operation_events = "/events"
__operation_elements = "/elements"
__operation_monitors = "/monitors"

__resolver = Resolver(__endpoint, rest_crud.base_endpoint_with_workspace)

meta_key = 'result id'
gprint = print


@click.command()
@click.option('--template', help="A built-in known report type or the file path to the .j2 template. Built-in types include:    'builtin:transactions-csv'     'builtin:transactions-json'")
@click.option('--json-in', help="The file path to the .json data if previously stored using --out-file and no template or a json template")
@click.option('--out-file', help="The file path to the resulting output, or none to print to stdout")
@click.option('--filter', help="A filter statement to scope to a timespan and/or specify which reports and elements to use for multi-result analysis")
@click.argument('report_type',
                type=click.Choice(['single','trends'], case_sensitive=False),
                required=False)
@click.argument("name", type=str, required=False)
def cli(report_type, template, json_in, out_file, filter, name):
    """Generate builtin or custom Jinja reports based on test results data
    Example: neoload report --template builtin:transactions-csv single cur
    """

    global gprint

    json_data_text = None
    template_text = None
    final_output = None

    logger = logging.getLogger()

    filter_spec = parse_filter_spec(filter)
    time_filter = filter_spec['time_filter']
    results_filter = filter_spec['results_filter']
    elements_filter = filter_spec['elements_filter']
    exclude_filter = filter_spec['exclude_filter']

    components = get_default_components(True,exclude_filter)

    if out_file is None: gprint = lambda msg: logger.info(msg)

    if template is not None:

        if template.lower().startswith("builtin:transactions"):
            components = get_default_components(False,exclude_filter)
            components['transactions'] = True
            if template.lower().endswith("-csv"):
                template_text = get_builtin_template_transaction_csv()
            else:
                template_text = ""

        elif os.path.isfile(template):
            template_text = get_file_text(template)

        else:
            tools.system_exit({'message': "template value is not a file or a known type", 'code': 2})
            return


    if not json_in is None:
        json_data_text = get_file_text(json_in) if json_in is not None else None
    else:
        # no in file, so go out to source live

        if report_type == "single":
            data = get_single_report(name,components,time_filter,elements_filter,exclude_filter)
        elif report_type == "trends":
            data = get_trends_report(time_filter,results_filter,elements_filter,exclude_filter)
        else:
            tools.system_exit({'message': "No report_type named '" + report_type + "'.", 'code': 2})
            return

        json_data_text = json.dumps(data, indent=2)


    if json_data_text is None:
        # use default
        json_data_text = '{"summary":{"name": "empty"}}'

    if template_text is None or template_text == "":
        final_output = json_data_text
    else:
        dirname = os.path.dirname(os.path.abspath(template))
        loader = jinja2.FileSystemLoader(searchpath=dirname)
        env = jinja2.Environment(loader=loader)
        t = env.from_string(template_text)

        dict = json.loads(json_data_text)
        final_output = t.render(dict)


    if out_file is not None:
        set_file_text(out_file, final_output)

        if sys.stdin.isatty() and (out_file.lower().endswith(".html") or out_file.lower().endswith(".htm")):
            webbrowser.open_new_tab("file://" + out_file)

    else:
        print(final_output)

def parse_filter_spec(filter_spec):

    ret = {}
    ret['time_filter'] = None
    ret['results_filter'] = None
    ret['elements_filter'] = None
    ret['exclude_filter'] = None

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

    return ret


def add_component_if_not(components,key,default,exclude_list):
    components[key] = default if not key in components else components[key]
    #logging.getLogger().debug('exclude_list: ' + exclude_list + '; key: ' + key)
    if exclude_list is not None and key in exclude_list.split(","):
        components[key] = False

def get_default_components(default_retrieve=True,exclude_list=None):
    components = {}
    add_if_not = lambda key, default: add_component_if_not(components,key,default,exclude_list)
    add_if_not('summary',default_retrieve)
    add_if_not('statistics',default_retrieve)
    add_if_not('slas',default_retrieve)
    add_if_not('events',default_retrieve)
    add_if_not('transactions',default_retrieve)
    add_if_not('all_requests',default_retrieve)
    add_if_not('ext_data',default_retrieve)
    add_if_not('controller_points',default_retrieve)
    return components

def get_single_report(name,components=None,time_filter=None,elements_filter=None,exclude_filter=None):

    if components is None: components = get_default_components(True,exclude_filter)

    if name == "cur":
        name = user_data.get_meta(meta_key)
    is_id = tools.is_id(name)

    __id = tools.get_id(name, __resolver, is_id)

    if not __id:
        __id = user_data.get_meta_required(meta_key)

    json_data_text = ""

    json_result = {}
    json_stats = {}
    json_sla_global = {}
    json_sla_test = {}
    json_sla_interval = {}
    json_events = {}
    json_elements_transactions = {}
    json_elements_all_requests = None
    ext_datas = {}
    ctrl_datas = {}

    time_binding = None
    if time_filter is not None:
        time_binding = {
            "time_filter": time_filter
        }

    if components['summary'] or components['slas'] or time_filter is not None:
        gprint("Getting test results...")
        json_result = rest_crud_get(get_end_point(__id))
        json_result = add_test_result_summary_fields(json_result)
        if time_binding is not None:
            time_binding["summary"] = json_result
            time_binding = fill_time_binding(time_binding)

    if components['slas']:
        status = json_result['status']
        gprint("Getting global SLAs...")
        json_sla_global = [] if status!='TERMINATED' else rest_crud_get(get_end_point(__id, __operation_sla_global))
        gprint("Getting per-test SLAs...")
        json_sla_test = [] if status!='TERMINATED' else rest_crud_get(get_end_point(__id, __operation_sla_test))
        gprint("Getting per-interval SLAs...")
        json_sla_interval = rest_crud_get(get_end_point(__id, __operation_sla_interval))

    if components['statistics']:
        gprint("Getting test statistics...")
        json_stats = rest_crud_get(get_end_point(__id, __operation_statistics))

    if components['events']:
        gprint("Getting events...")
        json_events = rest_crud_get(get_end_point(__id, __operation_events))

    statistics_list = ["AVG_DURATION","MIN_DURATION","MAX_DURATION","COUNT","THROUGHPUT",
                        "ELEMENTS_PER_SECOND","ERRORS","ERRORS_PER_SECOND","ERROR_RATE",
                        "AVG_TTFB","MIN_TTFB","MAX_TTFB"]

    if components['all_requests']:
        gprint("Getting all-request data...")
        json_elements_requests = rest_crud_get(get_end_point(__id, __operation_elements) + "?category=REQUEST")
        json_elements_all_requests = list(filter(lambda m: m['id'] == 'all-requests', json_elements_requests))
        if not elements_filter is None:
            json_elements_all_requests = filter_elements(json_elements_all_requests, elements_filter)
        json_elements_all_requests = get_elements_data(__id, json_elements_all_requests, time_binding, True, statistics_list)


    if components['transactions']:
        gprint("Getting transactions...")
        json_elements_transactions = rest_crud_get(get_end_point(__id, __operation_elements) + "?category=TRANSACTION")
        if not elements_filter is None:
            json_elements_transactions = filter_elements(json_elements_transactions, elements_filter)
        json_elements_transactions = get_elements_data(__id, json_elements_transactions, time_binding, True, statistics_list)
        json_elements_transactions = list(sorted(json_elements_transactions, key=lambda x: x['display_name']))

    if components['ext_data'] or components['controller_points']:
        gprint("Getting monitors...")
        json_monitors = rest_crud_get(get_end_point(__id, __operation_monitors))

    if components['ext_data']:
        ext_datas = get_mon_datas(__id, lambda m: m['path'][0] == 'Ext. Data', json_monitors, True)
        ext_datas = list(sorted(ext_datas, key=lambda x: x['display_name']))

    if components['controller_points']:
        ctrl_datas = get_mon_datas(__id, lambda m: m['path'][0] == 'Controller', json_monitors, True)

    data = {
        'id': __id,
        'summary': json_result,
        'statistics': json_stats,
        'sla_global': json_sla_global,
        'sla_test': json_sla_test,
        'sla_interval': json_sla_interval,
        'events': json_events,
        'elements': {
            'transactions': json_elements_transactions
        },
        'all_requests': json_elements_all_requests[0] if json_elements_all_requests is not None else {},
        'ext_data': ext_datas,
        'controller_points': ctrl_datas,
    }
    return data

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
    except:
        raise ValueError("Something went wrong while fill_time_binding")


time_part_mod_to_sec = {
    "h": lambda x: x * 60 * 60,
    "m": lambda x: x * 60,
    "s": lambda x: x
}
def translate_time_part_to_seconds(total_duration_sec, part_spec):
    try:
        if part_spec.endswith("%"):
            return (int(part_spec.replace("%","")) / 100.0) * total_duration_sec
        else:
            secs = 0
            str = part_spec.strip()

            for key in time_part_mod_to_sec:
                arr = str.split(key)
                if arr[0].isdigit():
                    secs += time_part_mod_to_sec[key](int(arr[0]))
                    str = str.replace(arr[0]+key,"",1)

            if len(str) > 0:
                raise ValueError("Characters left over in timespan part spec, invalid: '" + str + "'")

            return secs

    except Exception:
        raise ValueError("Value of filter timespan part '" + part_spec + "' is invalid.")

def get_trends_report(time_binding, results_filter, elements_filter):
    # report_filter examples
    #
    filter_parts = results_filter.split("|") if results_filter is not None else []
    arr_ids = []
    arr_directives = []
    for part in filter_parts:
        if is_guid(part):
            arr_ids.append({
                "id": part,
                "type": "result"
            })
        else:
            arr_directives.append(part)
    #gprint(json.dumps(arr_ids))
    #gprint(json.dumps(arr_directives))

    if len(arr_ids) > 0:
        count_back = 0 # negative
        count_ahead = 0 # positive
        for d in arr_directives:
            if d.startswith("+") and is_integer(d):
                count_ahead = int(d)
            elif d.startswith("-") and is_integer(d):
                count_back = int(d)

        base_id = arr_ids[0]["id"]
        arr_results = get_results_by_result_id(base_id)
        arr_sorted_by_time = list(sorted(arr_results, key=lambda x: x["startDate"]))
        base_index = list(map(lambda x: x["id"],arr_sorted_by_time)).index(base_id)
        arr_selected = []

        for i in range(base_index,base_index+1+count_ahead):
            arr_selected.append(arr_sorted_by_time[i])
        for i in range(base_index+count_back,base_index):
            arr_selected.append(arr_sorted_by_time[i])

        arr_selected = list(sorted(arr_selected, key=lambda x: x["startDate"]))
        for i in range(0,len(arr_selected)):
            arr_selected[i]["index"] = i

        # gprint("\n".join(map(lambda x: json.dumps({
        #     "id": x["id"] ,
        #     "name": x["name"] ,
        #     "startDate": x["startDate"] ,
        # }),arr_selected)))
        # return

        all_transactions = []

        for result in arr_selected:
            gprint("Getting test '" + result["name"] + "' statistics...")
            __id = result["id"]
            result = add_test_result_summary_fields(result)
            json_stats = rest_crud_get(get_end_point(__id, __operation_statistics))

            found_elements = []
            if elements_filter is not None:
                elements = []
                # elements.extend(rest_crud_get(get_end_point(__id, __operation_elements) + "?category=REQUEST"))
                transactions = rest_crud_get(get_end_point(__id, __operation_elements) + "?category=TRANSACTION")
                elements.extend(transactions)
                found_elements = filter_elements(elements, elements_filter)
                found_elements = get_elements_data(__id, found_elements, time_binding, False, [])
                found_elements = sorted(found_elements, key=lambda x: x["aggregate"]["avgDuration"], reverse=True)
                all_transactions.extend(list(filter(lambda el: el["type"]=="TRANSACTION", found_elements)))

            result["elements"] = found_elements
            # filter by id OR name
            #
            result["statistics"] = json_stats

        all_transaction_names = list(map(lambda t: t["name"], all_transactions))
        unique_transaction_names = unique(all_transaction_names)

        unique_transactions = []
        transaction_aggregates = ["avgDuration","elementPerSecond","percentile50","percentile90","percentile95","percentile99"]
        for name in unique_transaction_names:
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
                    aggregates[agg].extend(list(map(lambda el: el["aggregate"][agg], els)))

            group["aggregate"] = {}
            for agg in transaction_aggregates:
                group["aggregate"]["max_"+agg]=max(aggregates[agg])

            unique_transactions.append(group)

        return {
            "summary": {
                "title": "Comparison"
            },
            "unique_transactions": unique_transactions,
            "results": arr_selected,
        }

    return None

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
        filters = list(map(lambda s: {
            "type": "id" if is_guid(s) else "regex",
            "value": s if is_guid(s) else re.compile(s),
        }, elements_filter.split("|")))
        for fil in filters:
            if fil["type"] == "id":
                found.extend(list(filter(lambda el: el["id"] == fil["value"], elements)))
            elif fil["type"] == "regex":
                found.extend(list(filter(lambda el: element_matches_regex(el, fil["value"]), elements)))
            else:
                raise ValueError
    return found

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

def get_results_by_result_id(__id):
    result = rest_crud_get(get_end_point(__id))
    project = result["project"]
    results = rest_crud_get(__endpoint+"?project="+project)
    return results

def get_end_point(id_test: str, operation=''):
    slash_id_test = '' if id_test is None else '/' + id_test
    return rest_crud.base_endpoint_with_workspace() + __endpoint + slash_id_test + operation


def get_file_text(path):
    text = None
    with open(path, 'r') as f:
        text = f.read()
    return text

def set_file_text(path,content):
    with open(path, 'w') as f:
        f.write(content)

def percentile(N, percent, key=lambda x:x):
    """
    Find the percentile of a list of values.

    @parameter N - is a list of values. Note N MUST BE already sorted.
    @parameter percent - a float value from 0.0 to 1.0.
    @parameter key - optional key function to compute value from each element of N.

    @return - the percentile of the values
    """
    if not N:
        return None
    k = (len(N)-1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return key(N[int(k)])
    d0 = key(N[int(f)]) * (c-k)
    d1 = key(N[int(c)]) * (k-f)
    return d0+d1

def get_human_readable_time(reldel):
    attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
    human_readable = lambda delta: ['%d %s' % (getattr(delta, attr), getattr(delta, attr) > 1 and attr or attr[:-1])
        for attr in attrs if getattr(delta, attr)]
    return human_readable(reldel)

def get_elements_data(result_id, base_col, time_binding, include_points, statistics_list):

    procedure = lambda el: get_element_data(el, result_id, time_binding, include_points, statistics_list)

    with concurrent.futures.ThreadPoolExecutor() as executor: #ThreadPoolExecutor
        for out in executor.map(procedure, base_col, chunksize=3):
            logging.getLogger().info('parallel processing get_element_data workers')

    #for el in base_col:
    #    get_element_data(el, result_id, include_points, statistics_list)
    return base_col

def get_element_data(el, result_id, time_binding, include_points, statistics_list):
    full_name = el['name'] if not 'path' in el else " \ ".join(el['path'])
    parent = get_element_parent(el)
    user_path = get_element_user_path(el)
    gprint("Getting element values for '" + full_name + "'")
    json_values = rest_crud_get(get_end_point(result_id, __operation_elements) + "/" + el['id'] + "/values")
    json_points = [] if not (include_points or time_binding is not None) else rest_crud_get(get_end_point(result_id, __operation_elements) + "/" + el['id'] + "/points?statistics=" + ",".join(statistics_list))

    if not time_binding is None:
        json_points = filter_by_time(json_points, time_binding, lambda p: int(p['from'])/1000, lambda p: int(p['to'])/1000)

        # check if list is empty on all aggregates
        perc_points = list(sorted(map(lambda x: x['AVG_DURATION'], json_points)))
        sumOfCount = 0 if len(json_points) < 1 else round(sum(list(map(lambda x: x['COUNT'], json_points))),1)
        sumOfErrors = 0 if len(json_points) < 1 else round(sum(list(map(lambda x: x['ERRORS'], json_points))),1)
        json_values['minDuration'] = 0 if len(json_points) < 1 else min(list(map(lambda x: x['MIN_DURATION'], json_points)))
        json_values['maxDuration'] = 0 if len(json_points) < 1 else max(list(map(lambda x: x['MAX_DURATION'], json_points)))
        json_values['avgDuration'] = 0 if len(json_points) < 1 else statistics.mean(list(map(lambda x: x['AVG_DURATION'], json_points)))
        json_values['count'] = round(sumOfCount, 1)
        json_values['percentile50'] = 0 if len(perc_points) < 1 else percentile(perc_points,0.5)
        json_values['percentile90'] = 0 if len(perc_points) < 1 else percentile(perc_points,0.9)
        json_values['percentile95'] = 0 if len(perc_points) < 1 else percentile(perc_points,0.95)
        json_values['percentile99'] = 0 if len(perc_points) < 1 else percentile(perc_points,0.99)
        json_values['successCount'] = sumOfCount - sumOfErrors
        json_values['successRate'] = 0 if sumOfCount == 0 else json_values['successCount'] / sumOfCount
        json_values['failureCount'] = sumOfErrors
        json_values['failureRate'] = 0 if sumOfCount == 0 else json_values['failureCount'] / sumOfCount

# {
#   "count": 0,
#   "elementPerSecond": 0,
#   "minDuration": 0,
#   "maxDuration": 0,
#   "sumDuration": 0,
#   "avgDuration": 0,
#   "minTTFB": 0,
#   "maxTTFB": 0,
#   "sumTTFB": 0,
#   "avgTTFB": 0,
#   "sumDownloadedBytes": 0,
#   "downloadedBytesPerSecond": 0,
#   "successCount": 0,
#   "successPerSecond": 0,
#   "successRate": 0,
#   "failureCount": 0,
#   "failurePerSecond": 0,
#   "failureRate": 0,
#   "percentile50": 0,
#   "percentile90": 0,
#   "percentile95": 0,
#   "percentile99": 0
# }
# {
#     "from": 0,
#     "to": 0,
#     "AVG_DURATION": 0,
#     "MIN_DURATION": 0,
#     "MAX_DURATION": 0,
#     "COUNT": 0,
#     "THROUGHPUT": 0,
#     "ELEMENTS_PER_SECOND": 0,
#     "ERRORS": 0,
#     "ERRORS_PER_SECOND": 0,
#     "ERROR_RATE": 0,
#     "AVG_TTFB": 0,
#     "MIN_TTFB": 0,
#     "MAX_TTFB": 0,
#     "AVG": 0
#   }
    perc_fields = list(filter(lambda x: x.startswith('percentile'), json_values.keys()))
    convert_to_seconds = ['minDuration','maxDuration','sumDuration','avgDuration'] \
                        + perc_fields
    for field in convert_to_seconds:
        if field in json_values:
            if json_values[field] is None:
                raise ValueError("Field '" + field + "' is None")
            else:
                json_values[field] = json_values[field] / 1000.0

    round_fields = convert_to_seconds \
                    + ['successRate','failureRate']
    for field in round_fields:
        if field in json_values:
            json_values[field] = round(json_values[field],3)

    el["display_name"] = full_name
    el["parent"] = parent
    el["user_path"] = user_path
    el["aggregate"] = json_values
    el["points"] = json_points
    el["totalCount"] = el["aggregate"]["successCount"] + el["aggregate"]["failureCount"]
    el["successRate"] = 0 if el["totalCount"] == 0 else el["aggregate"]["successCount"] / el["totalCount"]
    el["failureRate"] = 0 if el["totalCount"] == 0 else el["aggregate"]["failureCount"] / el["totalCount"]
    return el

def filter_by_time(objs, time_binding, from_function, to_function):
    ret = []
    from_time = time_binding["from_secs"]
    to_time = time_binding["to_secs"]
    for obj in objs:
        this_from = from_function(obj)
        this_to = to_function(obj)
        if this_from >= from_time:
            if this_to <= to_time:
                ret.append(obj)
    return ret


def get_mon_datas(result_id, l_selector, base_col, include_points):
    mons = []
    for mon in list(filter(l_selector, base_col)):
        mons.append(mon)
    for mon in mons:
        full_name = mon['name'] if not 'path' in mon else " \ ".join(mon['path'])
        gprint("Getting monitor values for '" + full_name + "'")
        mon_points = rest_crud_get(get_end_point(result_id, __operation_monitors) + "/" + mon['id'] + "/points")
        time_points = list(sorted(mon_points, key=lambda x: x['from']))
        perc_points = list(sorted(map(lambda x: x['AVG'], mon_points)))
        mon["display_name"] = full_name
        #txn["points"] = json_extdata_points
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
    for txn in elements.transactions | rejectattr('id', 'equalto', 'all-transactions') | rejectattr('aggregate.count', 'equalto', '0') | sort(attribute='avgDuration',reverse=true) %}
{{ txn.user_path|e }};{{ txn.name|e }};{{ txn.parent|e }};{{ txn.aggregate.count }};{{ txn.aggregate.minDuration }};{{ txn.aggregate.avgDuration }};{{ txn.aggregate.maxDuration }};{{ txn.aggregate.percentile50 }};{{ txn.aggregate.percentile90 }};{{ txn.aggregate.percentile95 }};{{ txn.aggregate.percentile99 }};{{ txn.aggregate.successCount }};{{ txn.aggregate.successRate }};{{ txn.aggregate.failureCount }};{{ txn.aggregate.failureRate }}{%
    endfor %}""".strip()

rest_calls = []
max_calls_per_second = ((300 - 50) / 60)
calls_indicator = 0

def cleanup_completed_calls():
    back_step = get_epoch() - (1000)
    l = list(filter(lambda a: a["completed"] and a["epoch"]<back_step, rest_calls))
    if len(l) > 20:
        logging.getLogger().debug("Cleaning up completed calls")
        for e in l:
            try:
                rest_calls.remove(e)
            except Exception:
                logging.getLogger().debug("Clean couldn't remove an e")

def get_incomplete_calls():
    return list(filter(lambda a: a["sent"] and not a["completed"], rest_calls))
def get_current_calls_per_second_rate():
    back_step = get_epoch() - (1000)
    l = len(list(filter(lambda a: a["sent"] and a["epoch"]>=back_step, rest_calls)))
    return l
def get_epoch():
    return time.time() * 1000
def rest_crud_get(url):
    global calls_indicator
    if calls_indicator > 20:
        cleanup_completed_calls()
        calls_indicator = 0

    call = {
        "uuid": uuid.uuid1(),
        "url": url,
        "epoch": get_epoch(),
        "sent": False,
        "completed": False,
    }
    rest_calls.append(call)
    call = next(filter(lambda a: a["uuid"] == call["uuid"],rest_calls))
    while get_current_calls_per_second_rate() >= max_calls_per_second:
        logging.getLogger().debug("Waiting due to rate: " + str(get_current_calls_per_second_rate()))
        time.sleep(0.200)

    call["sent"] = True
    calls_indicator += 1
    ret = rest_crud.get(url)
    call["completed"] = True
    return ret
