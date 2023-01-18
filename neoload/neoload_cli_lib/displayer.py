import junit_xml
from junit_xml import TestSuite, TestCase

from neoload_cli_lib.tools import print_color,__is_color_terminal
from neoload_cli_lib import tools
import colorama
import html

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
    print_color("SLA summary:")
    for sla in sla_json_global:
        __print_one_sla(__SLA_global.replace(' ', ''), sla)
    print_color('')
    for sla in sla_json_test:
        __print_one_sla(__SLA_test.replace(' ', ''), sla)
    print_color('')
    for sla in sla_json_interval:
        __print_one_sla(__SLA_interval.replace(' ', ''), sla)
    print_color('')


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
            where = ' [%.3f%% %s]' % (sla_json['warning'], build_threshold_str(sla_json['warningThreshold']))
        elif status == "FAILED":
            where = ' [%.3f%% %s]' % (sla_json['failed'], build_threshold_str(sla_json['failedThreshold']))

    return print_color("%sSLA [%s] %s on [%s%s]" % (kind, sla_json['kpi'], status, element, where), color)


def __get_color_from_status(status: str):
    return {
        "PASSED": "green",
        "WARNING": "yellow"
    }.get(status, "red")


def print_result_junit(json_result, sla_json_test, sla_json_interval, sla_json_global, junit_file_path):
    junit_suites = []
    for sla in sla_json_global:
        junit_suites.append(__build_test_suite(json_result, __SLA_global, sla))
    for sla in sla_json_test:
        junit_suites.append(__build_test_suite(json_result, __SLA_test, sla))
    for sla in sla_json_interval:
        junit_suites.append(__build_test_suite(json_result, __SLA_interval, sla))
    with open(junit_file_path, 'w') as stream:
        junit_xml.to_xml_report_file(stream, junit_suites, prettyprint=True)
    print('Report written to file %s' % junit_file_path)


def __build_test_suite(json_result, kind, sla_json):
    status = sla_json['status']

    if 'element' in sla_json.keys():
        category = sla_json['element']['category']
        user_path = sla_json['element']['userpath']
        suite_name = 'com.neotys.%s.%s%s' % (
            category, kind.replace(' ', ''), ('' if user_path == '' else '.%s' % user_path))
    else:
        suite_name = 'com.neotys.%s' % (kind.replace(' ', ''))

    test_name = sla_json['kpi']

    tc = TestCase(test_name, suite_name)
    if status == "FAILED": # or status == "WARNING":
        txt = __build_unit_test(json_result, kind, sla_json)
        tc.add_failure_info("SLA failed", txt, 'NeoLoad SLA')

    return TestSuite(suite_name, [tc])


def build_threshold_str(threshold):
    operation = threshold['operator']
    value = threshold.get('value') or threshold.get('values') or ''
    return f'between {value[0]} and {value[1]}' if operation == 'btw' else f'{operation} {value}'


def __build_unit_test(json_result, kind, sla_json):
    status = sla_json['status']

    reported = 0

    if kind == __SLA_test or kind == __SLA_global:
        reported = sla_json['value']
    elif status == "FAILED":
        reported = sla_json['failed']
    elif status == "WARNING":
        reported = sla_json['warning']

    threshold_str = ''

    if status == "FAILED":
        threshold_str = build_threshold_str(sla_json['failedThreshold'])
    if status == "WARNING":
        threshold_str = build_threshold_str(sla_json['warningThreshold'])

    text = ''

    if 'element' in sla_json.keys():
        element = sla_json['element']
        text += 'Container: %s<br/>' % element['name']
        text += 'Path: User Paths > %s > Init > %s > %s<br/>' % (element['userpath'], element['parent'], element['name'])
        text += 'Virtual User: %s<br/>' % element['userpath']
        text += 'SLA Profile: %s<br/>' % element['category']

    text += 'SLA Type: %s<br/>' % kind
    text += '%s Type: %s<br/>' % (status, sla_json['kpi'])
    text += 'Project: %s<br/>' % json_result['project']
    text += 'Scenario: %s<br/>' % json_result['scenario']
    text += '<br/>'
    text += '%s<br/>description: if the %s %s then fail<br/><br/>' % (status, sla_json['kpi'], threshold_str)
    text += 'Results: <br/><br/>'
    text += '%s=%s%%<br/><br/>' % (sla_json['kpi'], str(reported))
    text += 'Created N/A<br/>'

    text = text.replace('<br/>','\n')

    return text

def colorize_text(text):
    final = text

    is_color_term = __is_color_terminal()

    final = html.unescape(final)

    keys = []
    keys = keys + list(map(lambda x: 'Fore.'+x,colorama.Fore.__dict__.keys()))
    keys = keys + list(map(lambda x: 'Back.'+x,colorama.Back.__dict__.keys()))

    #print(keys)
    vals = {}
    for key in keys:
        vals[key] = eval("colorama."+key) if is_color_term else ""

    for val in vals:
        for chr in ['"',"'",""]:
            final = final.replace('<text color=' + chr + val + chr + '>', vals[val])

    final = final.replace("</text>", colorama.Style.RESET_ALL if is_color_term else "")

    return final
