import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'ls', 'create', 'get', 'patch', 'delete'
], case_sensitive=False), required=False)
@click.argument('reservation_id', type=str, required=False)
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for create, patch)')
def cli(command, reservation_id, input_file):
    """
    ls      # List reservations in the current workspace                .
    create  # Create a reservation (--file for JSON body)               .
    get     # Get a reservation by ID                                   .
    patch   # Update a reservation by ID (--file for JSON body)         .
    delete  # Delete a reservation by ID                                .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-reservations --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'ls':
        params = v4_endpoints.v4_workspace_params()
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('reservations'), params))

    elif command == 'create':
        body = _load_body(input_file)
        body = v4_endpoints.v4_inject_workspace(body)
        tools.print_json(rest_crud.post(v4_endpoints.v4_endpoint('reservations'), body))

    elif command == 'get':
        if not reservation_id:
            raise cli_exception.CliException('reservation_id is required for get')
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('reservations', reservation_id)
        ))

    elif command == 'patch':
        if not reservation_id:
            raise cli_exception.CliException('reservation_id is required for patch')
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(
            v4_endpoints.v4_endpoint('reservations', reservation_id), body
        ))

    elif command == 'delete':
        if not reservation_id:
            raise cli_exception.CliException('reservation_id is required for delete')
        response = rest_crud.delete(
            v4_endpoints.v4_endpoint('reservations', reservation_id)
        )
        if response.status_code == 204 or not response.content:
            print('Reservation deleted.')
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
