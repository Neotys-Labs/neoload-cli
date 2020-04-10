from termcolor import cprint
from neoload_cli_lib import tools


def print_result_summary(json_result, sla_json_global, sla_json_test, sla_json_interval, json_stats):
    print_sla(sla_json_global, sla_json_test, sla_json_interval)
    tools.print_json({
        'result': json_result,
        'statistics': json_stats
    })


def print_sla(sla_json_global, sla_json_test, sla_json_interval):
    cprint("SLA summary:")
    for sla in sla_json_global:
        __print_one_sla("Global", sla)
    cprint('')
    for sla in sla_json_test:
        __print_one_sla("PerRun", sla)
    cprint('')
    for sla in sla_json_interval:
        __print_one_sla("PerInterval", sla)
    cprint('')


def __print_one_sla(kind, sla_json):
    status = sla_json['status']
    color = "red" if status == "FAILED" else "green" if status == "PASSED" else "yellow"
    element = ''
    where = ''

    if 'element' in sla_json.keys():
        element = "{0} > {1} > {2}".format(
            sla_json['element']['userpath'],
            sla_json['element']['parent'],
            sla_json['element']['name']
        )

    if kind == "PerInterval":
        if status == "WARNING":
            threshold = sla_json['warningThreshold']
            where = ' [%.3f%% %s %s]' % (sla_json['warning'], threshold['operator'], threshold['value'])
        elif status == "FAILED":
            threshold = sla_json['failedThreshold']
            where = ' [%.3f%% %s %s]' % (sla_json['failed'], threshold['operator'], threshold['value'])

    return cprint("%sSLA [%s] %s on [%s%s]" % (kind, sla_json['kpi'], status, element, where), color)
