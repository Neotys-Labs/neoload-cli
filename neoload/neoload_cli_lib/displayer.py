from junit_xml import TestSuite, TestCase
from termcolor import cprint

from neoload_cli_lib import tools

__SLA_global = 'Global'
__SLA_test = 'Per Run'
__SLA_interval = 'Per Interval'


def print_result_summary(json_result, sla_json_global, sla_json_test, sla_json_interval, json_stats):
    __print_sla(sla_json_global, sla_json_test, sla_json_interval)
    tools.print_json({
        'result': json_result,
        'statistics': json_stats
    })


def __print_sla(sla_json_global, sla_json_test, sla_json_interval):
    cprint("SLA summary:")
    for sla in sla_json_global:
        __print_one_sla(__SLA_global.replace(' ', ''), sla)
    cprint('')
    for sla in sla_json_test:
        __print_one_sla(__SLA_test.replace(' ', ''), sla)
    cprint('')
    for sla in sla_json_interval:
        __print_one_sla(__SLA_interval.replace(' ', ''), sla)
    cprint('')


def __print_one_sla(kind, sla_json):
    status = sla_json['status']
    color = __get_color_from_status(status)
    element = ''
    where = ''

    if 'element' in sla_json.keys():
        element = "{0} > {1} > {2}".format(
            sla_json['element']['userpath'],
            sla_json['element']['parent'],
            sla_json['element']['name']
        )

    if kind == __SLA_interval.replace(' ', ''):
        if status == "WARNING":
            threshold = sla_json['warningThreshold']
            where = ' [%.3f%% %s %s]' % (sla_json['warning'], threshold['operator'], threshold['value'])
        elif status == "FAILED":
            threshold = sla_json['failedThreshold']
            where = ' [%.3f%% %s %s]' % (sla_json['failed'], threshold['operator'], threshold['value'])

    return cprint("%sSLA [%s] %s on [%s%s]" % (kind, sla_json['kpi'], status, element, where), color)


def __get_color_from_status(status: str):
    return {
        "PASSED": "green",
        "WARNING": "yellow"
    }.get(status, "red")


def print_result_junit(json_result, sla_json_test, sla_json_interval, junit_file_path):
    junit_suites = []
    for sla in sla_json_test:
        junit_suites.append(__build_test_suite(json_result, __SLA_test, sla))
    for sla in sla_json_interval:
        junit_suites.append(__build_test_suite(json_result, __SLA_interval, sla))
    with open(junit_file_path, 'w') as stream:
        TestSuite.to_file(stream, junit_suites, prettyprint=True)
    print('Report written to file %s' % junit_file_path)


def __build_test_suite(json_result, kind, sla_json):
    status = sla_json['status']
    category = sla_json['element']['category']
    user_path = sla_json['element']['userpath']
    suite_name = 'com.neotys.%s.%s%s' % (
        category, kind.replace(' ', ''), ('' if user_path == '' else '.%s' % user_path))
    test_name = sla_json['kpi']

    tc = TestCase(test_name, suite_name)
    if status == "FAILED" or status == "WARNING":
        txt = __build_unit_test(json_result, kind, sla_json)
        tc.add_failure_info("SLA failed", txt, 'NeoLoad SLA')

    return TestSuite(suite_name, [tc])


def __build_unit_test(json_result, kind, sla_json):
    status = sla_json['status']
    element = sla_json['element']
    reported = 0
    if kind == __SLA_test:
        reported = sla_json['value']
    elif status == "FAILED":
        reported = sla_json['failed']
    elif status == "WARNING":
        reported = sla_json['warning']

    operation = ''
    value = ''
    if kind == __SLA_interval:
        if status == "FAILED":
            threshold = sla_json['failedThreshold']
            operation = threshold['operator']
            value = threshold['value']
        if status == "WARNING":
            threshold = sla_json['warningThreshold']
            operation = threshold['operator']
            value = threshold['value']

    text = 'Container: %s<br/>' % element['name']
    text += 'Path: User Paths > %s > Init > %s > %s<br/>' % (element['userpath'], element['parent'], element['name'])
    text += 'Virtual User: %s<br/>' % element['userpath']
    text += 'SLA Profile: %s<br/>' % element['category']
    text += 'SLA Type: %s<br/>' % kind
    text += '%s Type: %s<br/>' % (status, sla_json['kpi'])
    text += 'Project: %s<br/>' % json_result['project']
    text += 'Scenario: %s<br/>' % json_result['scenario']
    text += '<br/>'
    text += '%s<br/>description: if the %s %s %s then fail<br/><br/>' % (status, sla_json['kpi'], operation, value)
    text += 'Results: <br/><br/>'
    text += '%s=%s%%<br/><br/>' % (sla_json['kpi'], str(reported))
    text += 'Created N/A<br/>'
    return text
