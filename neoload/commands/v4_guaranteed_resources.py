import json
import click
from neoload_cli_lib import rest_crud, tools, user_data, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'ls', 'create', 'patch', 'delete'
], case_sensitive=False), required=False)
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for create, patch)')
def cli(command, input_file):
    """
    ls        # List guaranteed resources in the current workspace        .
    create    # Create a guaranteed resource (--file for JSON body)       .
    patch     # Update guaranteed resources (--file for JSON body)        .
    delete    # Delete guaranteed resources                               .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-guaranteed-resources --help")
        return
    rest_crud.set_current_sub_command(command)

    workspace_id = user_data.get_meta('workspace id')
    if workspace_id is None:
        raise cli_exception.CliException(
            "No workspace set. Please use 'neoload workspaces use <id>' first."
        )

    if command == 'ls':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('workspaces', workspace_id, 'guaranteed-resources')
        ))

    elif command == 'create':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('workspaces', workspace_id, 'guaranteed-resources'),
            body
        ))

    elif command == 'patch':
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(
            v4_endpoints.v4_endpoint('workspaces', workspace_id, 'guaranteed-resources'),
            body
        ))

    elif command == 'delete':
        response = rest_crud.delete(
            v4_endpoints.v4_endpoint('workspaces', workspace_id, 'guaranteed-resources')
        )
        if response.status_code == 204 or not response.content:
            print('Guaranteed resources deleted.')
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
