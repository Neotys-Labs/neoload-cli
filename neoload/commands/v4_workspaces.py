import json
import urllib.parse
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_client, v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'ls', 'create', 'get', 'patch', 'delete',
    'members-ls', 'members-add', 'members-remove', 'subscription'
], case_sensitive=False), required=False)
@click.argument('id', type=str, required=False)
@click.option('--name', help='Workspace name')
@click.option('--login', help='User login for members-remove')
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file')
def cli(command, id, name, login, input_file):
    """
    ls                     # List all workspaces                                         .
    create                 # Create a workspace                                           .
    get <id>               # Get a workspace by ID                                        .
    patch <id>             # Update a workspace                                           .
    delete <id>            # Delete a workspace                                           .
    members-ls <id>        # List workspace members                                       .
    members-add <id>       # Add a member to a workspace (--file with userId, role)       .
    members-remove <id>    # Remove a member from a workspace (--login)                   .
    subscription <id>      # Get workspace subscription info                              .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-workspaces --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'ls':
        tools.print_json(_workspace_list())
        return

    if command == 'create':
        body = _build_body(input_file, name=name)
        tools.print_json(rest_crud.post(v4_endpoints.v4_endpoint('workspaces'), body))
        return

    # All remaining commands require id
    if not id:
        raise cli_exception.CliException('id is required for ' + command)

    if command == 'get':
        tools.print_json(v4_client.v4_get('workspaces', id))
        return

    if command == 'patch':
        body = _build_body(input_file, name=name)
        tools.print_json(v4_client.v4_update('workspaces', id, data=body))
        return

    if command == 'delete':
        result = v4_client.v4_delete('workspaces', id)
        if result:
            tools.print_json(result)
        else:
            print('Workspace deleted.')
        return

    if command == 'members-ls':
        tools.print_json(v4_client.v4_get('workspaces', id, 'members'))
        return

    if command == 'members-add':
        if not input_file:
            raise cli_exception.CliException('--file is required for members-add (JSON with userId and role)')
        try:
            body = json.load(input_file)
        except json.JSONDecodeError as err:
            raise cli_exception.CliException('%s\nThis command requires valid JSON input.' % str(err))
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('workspaces', id, 'members'), body))
        return

    if command == 'members-remove':
        if not login:
            raise cli_exception.CliException('--login is required for members-remove')
        endpoint = v4_endpoints.v4_endpoint('workspaces', id, 'members')
        query = urllib.parse.urlencode({'login': login})
        response = rest_crud.delete(endpoint + '?' + query)
        if response.content:
            tools.print_json(response.json())
        else:
            print('Member removed.')
        return

    if command == 'subscription':
        tools.print_json(v4_client.v4_get('workspaces', id, 'subscription'))
        return


def _workspace_list():
    """List all workspaces. Does NOT use v4_list (which injects workspaceId)."""
    page_number = 0
    page_size = 200
    all_items = []
    while True:
        response = rest_crud.get(
            v4_endpoints.v4_endpoint('workspaces'),
            {'pageNumber': page_number, 'pageSize': page_size}
        )
        items = response.get('items', [])
        all_items.extend(items)
        total = response.get('total', 0)
        if len(all_items) >= total or not items:
            break
        page_number += 1
    return all_items


def _build_body(input_file, name=None):
    body = {}
    if input_file:
        try:
            body = json.load(input_file)
        except json.JSONDecodeError as err:
            raise cli_exception.CliException(
                '%s\nThis command requires valid JSON input.' % str(err))
    if name is not None:
        body['name'] = name
    return body
