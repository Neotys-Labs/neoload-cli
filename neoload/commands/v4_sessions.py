import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'create', 'delete'
], case_sensitive=False), required=False)
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for create)')
def cli(command, input_file):
    """
    create    # Create a session (--file for JSON body)    .
    delete    # Delete current session                     .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-sessions --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'create':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(v4_endpoints.v4_endpoint('sessions'), body))
        return

    if command == 'delete':
        response = rest_crud.delete(v4_endpoints.v4_endpoint('sessions'))
        if response.content:
            tools.print_json(response.json())
        else:
            print('Session deleted.')
        return


def _load_body(input_file):
    """Load JSON body from file, or return empty dict if no file provided."""
    if not input_file:
        return {}
    try:
        return json.load(input_file)
    except json.JSONDecodeError as err:
        raise cli_exception.CliException(
            '%s\nThis command requires valid JSON input.' % str(err))
