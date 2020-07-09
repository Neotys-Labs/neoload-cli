import click
from neoload_cli_lib import cli_exception
import neoload_cli_lib.schema_validation as schema_validation
from jinja2 import Template
import json
import tempfile
import os
import webbrowser
import sys
import time

import math
import functools

from neoload_cli_lib import tools, rest_crud, user_data, displayer, cli_exception
from neoload_cli_lib.name_resolver import Resolver

from dateutil.relativedelta import relativedelta

__endpoint = "v2/test-results"
__operation_statistics = "/statistics"
__operation_events = "/events"
__operation_sla_global = "/slas/statistics"
__operation_sla_test = "/slas/per-test"
__operation_sla_interval = "/slas/per-interval"
__operation_elements = "/elements"
__operation_monitors = "/monitors"

__resolver = Resolver(__endpoint)

meta_key = 'result id'
gprint = print


@click.command()
@click.option('--template', help="The file path to the .j2 template")
@click.option('--json-in', help="The file path to the .json data")
@click.option('--json-out', help="The file path to the .json data")
@click.argument("name", type=str, required=False)
def cli(template, json_in, json_out, name):
    """Generate custom reports based on test results JSON data and a mustache template"""

    json_data_text = None

    use_stdout = True

    if not json_in is None:
        json_data_text = get_file_text(json_in) if json_in is not None else None
    else:

        if name == "cur":
            name = user_data.get_meta(meta_key)
        is_id = tools.is_id(name)

        __id = tools.get_id(name, __resolver, is_id)

        if not __id:
            __id = user_data.get_meta_required(meta_key)

        json_data_text = ""

        gprint("Getting test results...")
        json_result = rest_crud.get(get_end_point(__id))
        status = json_result['status']
        gprint("Getting global SLAs...")
        json_sla_global = [] if status!='TERMINATED' else rest_crud.get(get_end_point(__id, __operation_sla_global))
        gprint("Getting per-test SLAs...")
        json_sla_test = [] if status!='TERMINATED' else rest_crud.get(get_end_point(__id, __operation_sla_test))
        gprint("Getting per-interval SLAs...")
        json_sla_interval = rest_crud.get(get_end_point(__id, __operation_sla_interval))
        gprint("Getting test statistics...")
        json_stats = rest_crud.get(get_end_point(__id, __operation_statistics))
        gprint("Getting events...")
        json_events = rest_crud.get(get_end_point(__id, __operation_events))

        gprint("Getting transactions...")
        json_elements_transactions = rest_crud.get(get_end_point(__id, __operation_elements) + "?category=TRANSACTION")

        for txn in json_elements_transactions:
            full_name = txn['name'] if not 'path' in txn else " \ ".join(txn['path'])
            gprint("Getting transaction values for '" + full_name + "'")
            json_transaction_values = rest_crud.get(get_end_point(__id, __operation_elements) + "/" + txn['id'] + "/values")
            txn["display_name"] = full_name
            txn["aggregate"] = json_transaction_values
            txn["totalCount"] = txn["aggregate"]["successCount"] + txn["aggregate"]["failureCount"]

        json_elements_transactions = list(sorted(json_elements_transactions, key=lambda x: x['display_name']))

        gprint("Getting monitors...")
        json_monitors = rest_crud.get(get_end_point(__id, __operation_monitors))

        ext_datas = get_mon_datas(__id, lambda m: m['path'][0] == 'Ext. Data', json_monitors, False)
        ext_datas = list(sorted(ext_datas, key=lambda x: x['display_name']))

        ctrl_datas = get_mon_datas(__id, lambda m: m['path'][0] == 'Controller', json_monitors, True)

        json_result["startDateText"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(json_result['startDate']/1000))
        json_result["endDateText"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(json_result['endDate']/1000))
        json_result["durationText"] = ", ".join(get_human_readable_time(relativedelta(seconds=((json_result['endDate']-json_result['startDate'])/1000))))

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
            'ext_data': ext_datas,
            'controller_points': ctrl_datas,
        }

        json_data_text = json.dumps(data, indent=2)

        if json_out is not None:
            use_stdout = False
            set_file_text(json_out, json_data_text)


    template_text = get_file_text(template) if template is not None else None

    if template_text is None:
        # use default
        template_text = ""

    if json_data_text is None:
        # use default
        json_data_text = '{"summary":{"name": "empty"}}'

    t = Template(template_text)

    if use_stdout:
        dict = json.loads(json_data_text)
        output = t.render(dict)
        if sys.stdin.isatty():
            fd, path = tempfile.mkstemp()
            html_path = path+".html"
            try:
                with os.fdopen(fd, 'w') as tmp:
                    # do stuff with temp file
                    tmp.write(output)
            finally:
                os.rename(path, html_path)
                gprint(html_path)
                webbrowser.open_new_tab("file://" + html_path)
        else:
            gprint(output)

def get_end_point(id_test: str, operation=''):
    return __endpoint + "/" + id_test + operation

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

def get_mon_datas(result_id, l_selector, base_col, include_points):
    mons = []
    for mon in list(filter(l_selector, base_col)):
        mons.append(mon)
    for mon in mons:
        full_name = mon['name'] if not 'path' in mon else " \ ".join(mon['path'])
        gprint("Getting monitor values for '" + full_name + "'")
        mon_points = rest_crud.get(get_end_point(result_id, __operation_monitors) + "/" + mon['id'] + "/points")
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
