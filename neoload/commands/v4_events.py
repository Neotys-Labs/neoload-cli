import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'ls', 'create', 'get', 'patch', 'delete',
    'errors', 'statistics', 'content'
], case_sensitive=False), required=False)
@click.option('--result-id', required=True, help='Test result ID')
@click.option('--event-id', default=None, help='Event ID (required for get, patch, delete)')
@click.option('--content-id', default=None, help='Content ID (required for content)')
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for create, patch)')
def cli(command, result_id, event_id, content_id, input_file):
    """
    ls          # List events for a result                                   .
    create      # Create an event (--file for JSON body)                     .
    get         # Get an event (requires --event-id)                         .
    patch       # Patch an event (requires --event-id, --file for body)      .
    delete      # Delete an event (requires --event-id)                      .
    errors      # Get error events aggregation for a result                  .
    statistics  # Get event statistics for a result                          .
    content     # Get event content (requires --content-id)                  .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-events --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'ls':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'events')
        ))

    elif command == 'create':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('results', result_id, 'events'),
            body
        ))

    elif command == 'get':
        if not event_id:
            raise cli_exception.CliException('--event-id is required for get')
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'events', event_id)
        ))

    elif command == 'patch':
        if not event_id:
            raise cli_exception.CliException('--event-id is required for patch')
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(
            v4_endpoints.v4_endpoint('results', result_id, 'events', event_id),
            body
        ))

    elif command == 'delete':
        if not event_id:
            raise cli_exception.CliException('--event-id is required for delete')
        response = rest_crud.delete(
            v4_endpoints.v4_endpoint('results', result_id, 'events', event_id)
        )
        if response.status_code == 204 or not response.content:
            print('Event deleted.')
        else:
            tools.print_json(response.json())

    elif command == 'errors':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'events', 'errors')
        ))

    elif command == 'statistics':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'events', 'statistics')
        ))

    elif command == 'content':
        if not content_id:
            raise cli_exception.CliException('--content-id is required for content')
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'events', 'contents', content_id)
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
