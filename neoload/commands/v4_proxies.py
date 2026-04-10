import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'ls', 'create', 'patch', 'delete'
], case_sensitive=False), required=False)
@click.argument('proxy_id', type=str, required=False)
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for create, patch)')
def cli(command, proxy_id, input_file):
    """
    ls        # List all proxies                                          .
    create    # Create a proxy (--file for JSON body)                     .
    patch     # Update a proxy by ID (--file for JSON body)               .
    delete    # Delete a proxy by ID                                      .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-proxies --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'ls':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('proxies')))

    elif command == 'create':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(v4_endpoints.v4_endpoint('proxies'), body))

    elif command == 'patch':
        if not proxy_id:
            raise cli_exception.CliException('proxy_id is required for patch')
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(
            v4_endpoints.v4_endpoint('proxies', proxy_id), body
        ))

    elif command == 'delete':
        if not proxy_id:
            raise cli_exception.CliException('proxy_id is required for delete')
        response = rest_crud.delete(v4_endpoints.v4_endpoint('proxies', proxy_id))
        if response.status_code == 204 or not response.content:
            print('Proxy deleted.')
        else:
            tools.print_json(response.json())


def _load_body(input_file):
    """Load JSON body from file, or return empty dict if no file provided."""
    if not input_file:
        return {}
    try:
        return json.load(input_file)
    except json.JSONDecodeError as err:
        raise cli_exception.CliException(
            '%s\nThis command requires valid JSON input.' % str(err))
