import click
from neoload_cli_lib import rest_crud, tools
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'ls'
], case_sensitive=False), required=False)
@click.option('--result-id', required=True, help='Test result ID')
def cli(command, result_id):
    """
    ls  # List SLAs for a result  .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-slas --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'ls':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'slas')
        ))
