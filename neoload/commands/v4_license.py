import json
import click
from neoload_cli_lib import rest_crud, tools, user_data, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'get', 'install',
    'leases-ls', 'leases-create', 'leases-get',
    'activation-request', 'deactivation-request',
    'forced-release', 'release'
], case_sensitive=False), required=False)
@click.argument('lease_identifier', type=str, required=False)
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for install, leases-create, activation-request, deactivation-request, forced-release, release)')
def cli(command, lease_identifier, input_file):
    """
    get                   # GET current license info                                       .
    install               # Install a license (--file for JSON body)                       .
    leases-ls             # List offline leases (workspaceId optional)                     .
    leases-create         # Create an offline lease, requires workspace (--file for body)  .
    leases-get            # Download a lease file by ID                                    .
    activation-request    # Submit a license activation request (--file for JSON body)     .
    deactivation-request  # Submit a license deactivation request (--file for JSON body)   .
    forced-release        # Force-release a license (--file for JSON body)                 .
    release               # Release a license (--file for JSON body)                       .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-license --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'get':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('license')
        ))

    elif command == 'install':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('license'),
            body
        ))

    elif command == 'leases-ls':
        workspace_id = user_data.get_meta('workspace id')
        params = {'workspaceId': workspace_id} if workspace_id else None
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('license', 'leases'),
            params
        ))

    elif command == 'leases-create':
        body = _load_body(input_file)
        body = v4_endpoints.v4_inject_workspace(body)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('license', 'leases'),
            body
        ))

    elif command == 'leases-get':
        if not lease_identifier:
            raise cli_exception.CliException('lease_identifier is required for leases-get')
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('license', 'leases', lease_identifier)
        ))

    elif command == 'activation-request':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('license', 'activation-requests'),
            body
        ))

    elif command == 'deactivation-request':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('license', 'deactivation-requests'),
            body
        ))

    elif command == 'forced-release':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('license', 'forced-releases'),
            body
        ))

    elif command == 'release':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('license', 'releases'),
            body
        ))


def _load_body(input_file):
    """Load JSON body from file, or return empty dict if no file provided."""
    if not input_file:
        return {}
    try:
        return json.load(input_file)
    except json.JSONDecodeError as err:
        raise cli_exception.CliException(
            '%s\nThis command requires valid JSON input.' % str(err))
