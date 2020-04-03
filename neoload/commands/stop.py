import click
import json

from commands import test_results
from neoload_cli_lib import rest_crud, tools, user_data

__endpoint = "v2/tests-results/"


@click.command()
@click.option('--force', is_flag=True, help="force the stop of running tests")
@click.argument('name', required=False)
def cli(name, force):
    if not name:
        name = user_data.get_meta(test_results.meta_key)
    if not name:
        raise Exception('No test id is provided')

    policy = 'FORCE' if force else 'GRACEFUL'
    map_policy = {"stopPolicy": policy}
    if not tools.is_id(name):
        name = test_results.__resolver.resolve_name(name)

    if tools.confirm("Do you want stop the test" + name + " with " + policy.lower() + " policy ?"):
        rest_crud.post(__endpoint + "/" + name + "/stop", json.dumps(map_policy))
