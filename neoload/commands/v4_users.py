import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'ls', 'create', 'get', 'patch', 'delete',
    'workspaces-ls', 'workspaces-add', 'workspaces-remove'
], case_sensitive=False), required=False)
@click.argument('id', type=str, required=False)
@click.option('--workspace-id', default=None, help='Workspace ID (for workspaces-add body, workspaces-remove path)')
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for create, patch, workspaces-add)')
def cli(command, id, workspace_id, input_file):
    """
    ls                         # List all users                                                  .
    create                     # Create a user (--file for JSON body)                            .
    get <id>                   # Get a user by ID                                                .
    patch <id>                 # Update a user (--file for JSON body)                            .
    delete <id>                # Delete a user                                                   .
    workspaces-ls <id>         # List workspaces for a user                                      .
    workspaces-add <id>        # Add user to a workspace (--workspace-id or --file)              .
    workspaces-remove <id>     # Remove user from a workspace (--workspace-id)                   .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-users --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'ls':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('users')))
        return

    if command == 'create':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(v4_endpoints.v4_endpoint('users'), body))
        return

    # All remaining commands require id
    if not id:
        raise cli_exception.CliException('id is required for ' + command)

    if command == 'get':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('users', id)))
        return

    if command == 'patch':
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(v4_endpoints.v4_endpoint('users', id), body))
        return

    if command == 'delete':
        response = rest_crud.delete(v4_endpoints.v4_endpoint('users', id))
        if response.content:
            tools.print_json(response.json())
        else:
            print('User deleted.')
        return

    if command == 'workspaces-ls':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('users', id, 'workspaces')))
        return

    if command == 'workspaces-add':
        if workspace_id:
            body = {'workspaceId': workspace_id}
        else:
            body = _load_body(input_file)
        tools.print_json(rest_crud.put(
            v4_endpoints.v4_endpoint('users', id, 'workspaces'), body))
        return

    if command == 'workspaces-remove':
        if not workspace_id:
            raise cli_exception.CliException('--workspace-id is required for workspaces-remove')
        response = rest_crud.delete(
            v4_endpoints.v4_endpoint('users', id, 'workspaces', workspace_id))
        if response.content:
            tools.print_json(response.json())
        else:
            print('User removed from workspace.')
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
