import click

from commands import test_results
from neoload_cli_lib import tools, user_data, running_tools, cli_exception, rest_crud


@click.command()
@click.option('--force', is_flag=True, help="force the stop of running tests")
@click.argument('name', required=False)
def cli(name, force):
    """stop a test"""
    rest_crud.set_current_command()
    if not name or name == "cur":
        name = user_data.get_meta(test_results.meta_key)
    if not name:
        raise cli_exception.CliException('No test id is provided')

    if not tools.is_id(name):
        name = test_results.__resolver.resolve_name(name)

    running_tools.stop(name, force)
