import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'element-values', 'element-timeseries', 'element-percentiles',
    'monitor-values', 'monitor-timeseries',
    'intervals-ls', 'intervals-create', 'intervals-patch', 'intervals-delete',
    'interval-generation', 'report'
], case_sensitive=False), required=False)
@click.option('--result-id', required=True, help='Test result ID')
@click.option('--element-id', default=None, help='Element ID (required for element-timeseries, element-percentiles)')
@click.option('--monitor-id', default=None, help='Monitor ID (required for monitor-timeseries)')
@click.option('--interval-id', default=None, help='Interval ID (required for intervals-patch, intervals-delete)')
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for intervals-create, intervals-patch, interval-generation, report)')
def cli(command, result_id, element_id, monitor_id, interval_id, input_file):
    """
    element-values       # GET element values for a result                    .
    element-timeseries   # GET element timeseries (requires --element-id)     .
    element-percentiles  # GET element percentiles (requires --element-id)    .
    monitor-values       # GET monitor values for a result                    .
    monitor-timeseries   # GET monitor timeseries (requires --monitor-id)     .
    intervals-ls         # List intervals for a result                        .
    intervals-create     # Create an interval (--file for JSON body)          .
    intervals-patch      # Patch an interval (requires --interval-id)         .
    intervals-delete     # Delete an interval (requires --interval-id)        .
    interval-generation  # Trigger interval generation (--file for body)      .
    report               # Generate a report (--file for JSON body)           .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-analytics --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'element-values':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'elements', 'values')
        ))

    elif command == 'element-timeseries':
        if not element_id:
            raise cli_exception.CliException('--element-id is required for element-timeseries')
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'elements', element_id, 'timeseries')
        ))

    elif command == 'element-percentiles':
        if not element_id:
            raise cli_exception.CliException('--element-id is required for element-percentiles')
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'elements', element_id, 'percentiles')
        ))

    elif command == 'monitor-values':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'monitors', 'values')
        ))

    elif command == 'monitor-timeseries':
        if not monitor_id:
            raise cli_exception.CliException('--monitor-id is required for monitor-timeseries')
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'monitors', monitor_id, 'timeseries')
        ))

    elif command == 'intervals-ls':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'intervals')
        ))

    elif command == 'intervals-create':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('results', result_id, 'intervals'),
            body
        ))

    elif command == 'intervals-patch':
        if not interval_id:
            raise cli_exception.CliException('--interval-id is required for intervals-patch')
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(
            v4_endpoints.v4_endpoint('results', result_id, 'intervals', interval_id),
            body
        ))

    elif command == 'intervals-delete':
        if not interval_id:
            raise cli_exception.CliException('--interval-id is required for intervals-delete')
        response = rest_crud.delete(
            v4_endpoints.v4_endpoint('results', result_id, 'intervals', interval_id)
        )
        if response.status_code == 204 or not response.content:
            print('Interval deleted.')
        else:
            tools.print_json(response.json())

    elif command == 'interval-generation':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('results', result_id, 'interval-generation'),
            body
        ))

    elif command == 'report':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(
            v4_endpoints.v4_endpoint('results', result_id, 'report'),
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
