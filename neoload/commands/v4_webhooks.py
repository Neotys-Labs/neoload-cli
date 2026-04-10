import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'ls', 'create', 'get', 'patch', 'delete', 'validate'
], case_sensitive=False), required=False)
@click.argument('webhook_id', type=str, required=False)
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for create, patch, validate)')
def cli(command, webhook_id, input_file):
    """
    ls        # List webhooks in the current workspace                  .
    create    # Create a webhook (--file for JSON body)                 .
    get       # Get a webhook by ID                                     .
    patch     # Update a webhook by ID (--file for JSON body)           .
    delete    # Delete a webhook by ID                                  .
    validate  # Validate a webhook (POST /v4/webhooks/validation)       .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-webhooks --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'ls':
        params = v4_endpoints.v4_workspace_params()
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('webhooks'), params))

    elif command == 'create':
        body = _load_body(input_file)
        body = v4_endpoints.v4_inject_workspace(body)
        tools.print_json(rest_crud.post(v4_endpoints.v4_endpoint('webhooks'), body))

    elif command == 'get':
        if not webhook_id:
            raise cli_exception.CliException('webhook_id is required for get')
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('webhooks', webhook_id)))

    elif command == 'patch':
        if not webhook_id:
            raise cli_exception.CliException('webhook_id is required for patch')
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(
            v4_endpoints.v4_endpoint('webhooks', webhook_id), body
        ))

    elif command == 'delete':
        if not webhook_id:
            raise cli_exception.CliException('webhook_id is required for delete')
        response = rest_crud.delete(v4_endpoints.v4_endpoint('webhooks', webhook_id))
        if response.status_code == 204 or not response.content:
            print('Webhook deleted.')
        else:
            tools.print_json(response.json())

    elif command == 'validate':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('webhooks', 'validation'), body
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
