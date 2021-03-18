import time
from urllib.parse import quote

import click

from commands import test_settings, test_results
from neoload_cli_lib import running_tools, tools, rest_crud, user_data, hooks


@click.command()
@click.argument("name_or_id", type=str, required=False)
@click.option("--scenario", help="select scenario")
@click.option("--name", help="name of test results")
@click.option("--description", help="description of test results")
@click.option("--as-code", 'as_code', help="Comma-separated as-code files to use for the test.")
@click.option("--web-vu", 'web_vu', help="The number of Web Virtual Users to be reserved for the test.")
@click.option("--sap-vu", 'sap_vu', help="The number of SAP Virtual Users to be reserved for the test.")
@click.option("--cirix-vu", 'citrix_vu', help="The number of Citrix Virtual Users to be reserved for the test.")
@click.option("-d", "--detached", is_flag=True, help="Doesn't wait the end of test")
@click.option('--return-0', 'return_0', is_flag=True, default=False,
              help="return 0 when test is correctly launched, whatever the result of SLA")
def cli(name_or_id, scenario, detached, name, description, as_code, web_vu, sap_vu, citrix_vu, return_0):
    """run a test"""
    rest_crud.set_current_command()
    if not name_or_id or name_or_id == "cur":
        name_or_id = user_data.get_meta(test_settings.meta_key)

    is_id = tools.is_id(name_or_id)
    test_settings_json = tools.get_named_or_id(name_or_id, is_id, test_settings.__resolver)
    _id = test_settings_json['id']

    if scenario:
        rest_crud.patch(test_settings.get_end_point(_id), {'scenarioName': scenario})

    naming_pattern = name if name else test_settings_json['testResultNamingPattern']
    if not naming_pattern:
        naming_pattern = "#${runID}"
    naming_pattern = naming_pattern.replace('${runID}', str(test_settings_json['nextRunId']))

    hooks.trig("test.start", test_settings_json)

    # Sorry for that, post data are in the query string :'( :'(
    post_result = rest_crud.post(
        test_settings.get_end_point(_id) + '/start?' + create_data(naming_pattern, description, as_code, web_vu, sap_vu, citrix_vu),
        {})
    user_data.set_meta(test_settings.meta_key, _id)
    user_data.set_meta(test_results.meta_key, post_result['resultId'])
    # Wait 5 seconds until the test result is created.
    time.sleep(5)
    if not detached:
        running_tools.wait(post_result['resultId'], not return_0)
    else:
        tools.print_json(post_result)


def create_data(name, description, as_code, web_vu, sap_vu, citrix_vu):
    query = 'testResultName=' + quote(name)
    if description is not None:
        query += '&testResultDescription=' + quote(description)
    if as_code is not None:
        query += '&asCode=' + quote(as_code)
    if web_vu is not None:
        query += '&reservationWebVUs=' + web_vu
    if sap_vu is not None:
        query += '&reservationSAPVUs=' + sap_vu
    if citrix_vu is not None:
        query += '&reservationCitrixVUs=' + citrix_vu
    return query
