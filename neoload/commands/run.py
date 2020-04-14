from urllib.parse import quote
import click
from neoload_cli_lib import running_tools, tools, rest_crud, user_data
from commands import test_settings, test_results


@click.command()
@click.argument("name_or_id", type=str, required=False)
@click.option("--scenario", help="select scenario")
@click.option("--name", help="name of test results")
@click.option("-d", "--detached", help="Doesn't wait the end of test")
def cli(name_or_id, scenario, detached, name):
    """run a test"""
    if not name_or_id or name_or_id == "cur":
        name_or_id = user_data.get_meta(test_settings.meta_key)

    is_id = tools.is_id(name_or_id)
    test_settings_json = tools.get_named_or_id(name_or_id, is_id, test_settings.__resolver)
    _id = test_settings_json['id']

    if scenario:
        rest_crud.patch('v2/test_result/' + _id, {'scenarioName': scenario})

    naming_pattern = name if name else test_settings_json['testResultNamingPattern']
    if not naming_pattern:
        naming_pattern = "#${runID}"
    naming_pattern = naming_pattern.replace('${runID}', str(test_settings_json['nextRunId']))
    data = {
        'testResultName': naming_pattern
    }

    # Sorry for that, post data are in the query string :'( :'(
    post_result = rest_crud.post('v2/tests/%s/start?testResultName=%s' % (_id, quote(data['testResultName'])), data)
    user_data.set_meta(test_settings.meta_key, _id)
    user_data.set_meta(test_results.meta_key, post_result['resultId'])
    if not detached:
        running_tools.wait(post_result['resultId'])
    else:
        tools.print_json(post_result)
