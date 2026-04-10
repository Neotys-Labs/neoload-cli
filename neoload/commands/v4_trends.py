import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'get', 'patch', 'config-get', 'config-put', 'config-patch', 'elements'
], case_sensitive=False), required=False)
@click.option('--test-id', required=True, help='Test ID')
@click.option('--dry-run', is_flag=True, default=False, help='Dry-run mode for config-put')
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for patch, config-put, config-patch)')
def cli(command, test_id, dry_run, input_file):
    """
    get          # GET trends for a test                                      .
    patch        # PATCH trends for a test (--file for JSON body)             .
    config-get   # GET trends configuration for a test                       .
    config-put   # PUT trends configuration (--file, optional --dry-run)     .
    config-patch # PATCH trends configuration (--file for JSON body)         .
    elements     # GET trends elements for a test                             .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-trends --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'get':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('tests', test_id, 'trends')
        ))

    elif command == 'patch':
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(
            v4_endpoints.v4_endpoint('tests', test_id, 'trends'),
            body
        ))

    elif command == 'config-get':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('tests', test_id, 'trends', 'configuration')
        ))

    elif command == 'config-put':
        body = _load_body(input_file)
        endpoint = v4_endpoints.v4_endpoint('tests', test_id, 'trends', 'configuration')
        if dry_run:
            endpoint = endpoint + '?dryRun=true'
        tools.print_json(rest_crud.put(endpoint, body))

    elif command == 'config-patch':
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(
            v4_endpoints.v4_endpoint('tests', test_id, 'trends', 'configuration'),
            body
        ))

    elif command == 'elements':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('tests', test_id, 'trends', 'elements')
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
