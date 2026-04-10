import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'get', 'patch', 'password',
    'tokens-ls', 'tokens-create', 'tokens-delete',
    'features'
], case_sensitive=False), required=False)
@click.argument('token', type=str, required=False)
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for patch, password, tokens-create)')
def cli(command, token, input_file):
    """
    get                    # Get current user profile                                     .
    patch                  # Update current user profile (--file for JSON body)           .
    password               # Change current user password (--file for JSON body)          .
    tokens-ls              # List personal access tokens                                  .
    tokens-create          # Create a personal access token (--file for JSON body)        .
    tokens-delete <token>  # Delete a personal access token by name                      .
    features               # Get features available for current user                      .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-me --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'get':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('me')))
        return

    if command == 'patch':
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(v4_endpoints.v4_endpoint('me'), body))
        return

    if command == 'password':
        body = _load_body(input_file)
        tools.print_json(rest_crud.put(v4_endpoints.v4_endpoint('me', 'password'), body))
        return

    if command == 'tokens-ls':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('me', 'tokens')))
        return

    if command == 'tokens-create':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(v4_endpoints.v4_endpoint('me', 'tokens'), body))
        return

    if command == 'tokens-delete':
        if not token:
            raise cli_exception.CliException('token is required for tokens-delete')
        response = rest_crud.delete(v4_endpoints.v4_endpoint('me', 'tokens', token))
        if response.content:
            tools.print_json(response.json())
        else:
            print('Token deleted.')
        return

    if command == 'features':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('me', 'features')))
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
