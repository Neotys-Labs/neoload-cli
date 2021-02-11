import click

from commands import test_results
from neoload_cli_lib import running_tools, user_data, tools, rest_crud


@click.command()
@click.argument("name_or_id", type=str)
@click.option('--return-0', 'return_0', is_flag=True, default=False,
              help="return 0 when test is correctly launched, whatever the result of SLA")
def cli(name_or_id, return_0):
    """Wait the end of test"""
    rest_crud.set_current_command()
    if not name_or_id or name_or_id == "cur":
        name_or_id = user_data.get_meta(test_results.meta_key)

    id_ = tools.get_id(name_or_id, test_results.__resolver)

    running_tools.wait(id_, not return_0)
