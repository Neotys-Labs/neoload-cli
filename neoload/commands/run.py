import logging
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
@click.option("--cirix-vu", 'citrix_vu', hidden = True, help="The number of Citrix Virtual Users to be reserved for the test.") # deprecated option
@click.option("-d", "--detached", is_flag=True, help="Doesn't wait the end of test")
@click.option('--return-0', 'return_0', is_flag=True, default=False,
              help="return 0 when test is correctly launched, whatever the result of SLA")
@click.option('--external-url', 'external_url', help="URL to an external system, for example the CI job's link")
@click.option('--external-url-label', 'external_url_label',
              help="Label to describe the external URL, for example the CI name or job ID")
@click.option('--lock', is_flag=True, default=None,
              help="Protects the Test Result to avoid automatic or accidental manual deletion. In interactive mode (not detached), the Test Result won't be protected if the run fails to start.")
@click.option("--reservation-id", 'reservation_id', help="The reservation identifier to use for the test that can be retrieved from the NeoLoad Web reservation calendar URL (if the reservation mode is enabled)")
@click.option("--reservation-duration", 'reservation_duration', help="The duration (in seconds) of the reservation for the test (if the reservation mode is enabled)")

def cli(name_or_id, scenario, detached, name, description, as_code, web_vu, sap_vu, citrix_vu, return_0, external_url,
        external_url_label, lock, reservation_id, reservation_duration):
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
        test_settings.get_end_point(_id) + '/start?' + create_data(naming_pattern, description, as_code, web_vu, sap_vu, citrix_vu, reservation_id, reservation_duration),
        {})
    user_data.set_meta(test_settings.meta_key, _id)
    user_data.set_meta(test_results.meta_key, post_result['resultId'])
    # Wait 5 seconds until the test result is created.
    time.sleep(5)

    data_external_url = {}
    prepare_external_url(data_external_url, external_url, external_url_label)
    patch_data(post_result['resultId'], data_external_url)

    data_lock = {}
    prepare_lock(data_lock, lock)

    if not detached:
        running_tools.wait(post_result['resultId'], not return_0, data_lock)
    else:
        patch_data(post_result['resultId'], data_lock)
        tools.print_json(post_result)


def create_data(name, description, as_code, web_vu, sap_vu, citrix_vu, reservation_id, reservation_duration):
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
        logging.getLogger().warning('WARNING: --cirix-vu is deprecated')
        query += '&reservationCitrixVUs=' + citrix_vu
    if reservation_id is not None:
        query += '&reservationId=' + reservation_id
    if reservation_duration is not None:
        query += '&reservationDuration=' + reservation_duration
    return query


def prepare_external_url(data, external_url, external_url_label):
    if external_url is not None:
        data['externalUrl'] = external_url
    if external_url_label is not None:
        data['externalUrlLabel'] = external_url_label

def prepare_lock(data, lock):
    if lock is not None:
        data['isLocked'] = lock

def patch_data(result_id, data):
    if len(data) != 0:
        test_results.print_compatibility_warning_for_old_nlw(data)
        if not user_data.is_version_lower_than('2.10.0'):
            rest_crud.patch(test_results.get_end_point(result_id), data)