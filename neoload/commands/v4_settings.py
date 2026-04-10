import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'get', 'patch', 'information', 'subscription'
], case_sensitive=False), required=False)
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for patch)')
def cli(command, input_file):
    """
    get             # Get account settings                              .
    patch           # Update account settings (--file for JSON body)   .
    information     # Get account information                          .
    subscription    # Get subscription information                     .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-settings --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'get':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('settings')))
        return

    if command == 'patch':
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(v4_endpoints.v4_endpoint('settings'), body))
        return

    if command == 'information':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('information')))
        return

    if command == 'subscription':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('subscription')))
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
