import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'config-get', 'config-patch',
    'entities-ls', 'entities-create', 'entities-patch', 'entities-delete',
    'search-users', 'search-groups', 'search-user-groups'
], case_sensitive=False), required=False)
@click.argument('id', type=str, required=False)
@click.option('--login', default=None, help='User login (required for search-user-groups)')
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for config-patch, entities-create, entities-patch, search-*)')
def cli(command, id, login, input_file):
    """
    config-get                     # Get LDAP configuration                                          .
    config-patch                   # Update LDAP configuration (--file for JSON body)                .
    entities-ls                    # List LDAP authorized entities                                   .
    entities-create                # Create an authorized entity (--file for JSON body)              .
    entities-patch <id>            # Update an authorized entity (--file for JSON body)              .
    entities-delete <id>           # Delete an authorized entity                                     .
    search-users                   # Search LDAP users (--file for JSON body)                        .
    search-groups                  # Search LDAP groups (--file for JSON body)                       .
    search-user-groups             # Search groups for a user (--login, --file for JSON body)        .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-ldap --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'config-get':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('ldap', 'configuration')))
        return

    if command == 'config-patch':
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(v4_endpoints.v4_endpoint('ldap', 'configuration'), body))
        return

    if command == 'entities-ls':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('ldap', 'authorized-entities')))
        return

    if command == 'entities-create':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('ldap', 'authorized-entities'), body))
        return

    if command == 'entities-patch':
        if not id:
            raise cli_exception.CliException('id is required for entities-patch')
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(
            v4_endpoints.v4_endpoint('ldap', 'authorized-entities', id), body))
        return

    if command == 'entities-delete':
        if not id:
            raise cli_exception.CliException('id is required for entities-delete')
        response = rest_crud.delete(
            v4_endpoints.v4_endpoint('ldap', 'authorized-entities', id))
        if response.content:
            tools.print_json(response.json())
        else:
            print('Authorized entity deleted.')
        return

    if command == 'search-users':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('ldap', 'users', 'search'), body))
        return

    if command == 'search-groups':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('ldap', 'groups', 'search'), body))
        return

    if command == 'search-user-groups':
        if not login:
            raise cli_exception.CliException('--login is required for search-user-groups')
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('ldap', 'users', login, 'groups', 'search'), body))
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
