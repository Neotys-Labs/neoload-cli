import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'ls', 'create', 'get', 'patch', 'delete', 'refs', 'checkout', 'checkout-status'
], case_sensitive=False), required=False)
@click.argument('repository_id', type=str, required=False)
@click.option('--checkout-id', default=None, help='Checkout ID (required for checkout-status)')
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for create, patch, checkout)')
def cli(command, repository_id, checkout_id, input_file):
    """
    ls               # List SCM repositories                                  .
    create           # Create an SCM repository (--file for JSON body)        .
    get              # Get an SCM repository by ID                            .
    patch            # Update an SCM repository by ID (--file for JSON body)  .
    delete           # Delete an SCM repository by ID                         .
    refs             # List references for an SCM repository                  .
    checkout         # Create a checkout (POST /v4/checkouts, --file for body).
    checkout-status  # Get checkout status (requires --checkout-id)           .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-scm-repositories --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'ls':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('scm-repositories')))

    elif command == 'create':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(v4_endpoints.v4_endpoint('scm-repositories'), body))

    elif command == 'get':
        if not repository_id:
            raise cli_exception.CliException('repository_id is required for get')
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('scm-repositories', repository_id)
        ))

    elif command == 'patch':
        if not repository_id:
            raise cli_exception.CliException('repository_id is required for patch')
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(
            v4_endpoints.v4_endpoint('scm-repositories', repository_id), body
        ))

    elif command == 'delete':
        if not repository_id:
            raise cli_exception.CliException('repository_id is required for delete')
        response = rest_crud.delete(
            v4_endpoints.v4_endpoint('scm-repositories', repository_id)
        )
        if response.status_code == 204 or not response.content:
            print('SCM repository deleted.')
        else:
            tools.print_json(response.json())

    elif command == 'refs':
        if not repository_id:
            raise cli_exception.CliException('repository_id is required for refs')
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('scm-repositories', repository_id, 'references')
        ))

    elif command == 'checkout':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(v4_endpoints.v4_endpoint('checkouts'), body))

    elif command == 'checkout-status':
        if not checkout_id:
            raise cli_exception.CliException('--checkout-id is required for checkout-status')
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('checkouts', checkout_id)
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
