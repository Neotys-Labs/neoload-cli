import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_client, v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'ls', 'create', 'get', 'patch', 'delete'
], case_sensitive=False), required=False)
@click.argument('zone_id', type=str, required=False)
@click.option('--name', help='Zone name')
@click.option('--description', help='Zone description')
@click.option('--type', 'zone_type', type=click.Choice(['STATIC', 'DYNAMIC', 'CLOUD'],
              case_sensitive=False), help='Zone type filter (ls) or value (create/patch)')
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file')
def cli(command, zone_id, name, description, zone_type, input_file):
    """
    ls     # Lists all zones (not workspace-scoped), optional --type filter   .
    create # Create a new zone                                                 .
    get    # Get a zone by ID                                                  .
    patch  # Replace a zone (PUT) by ID                                       .
    delete # Delete a zone by ID                                               .
    """
    if not command:
        print("command is mandatory. Please see neoload v4-zones --help")
        return

    if command == 'ls':
        params = {}
        if zone_type:
            params['type'] = zone_type.upper()
        tools.print_json(_zone_list(params))
        return

    if command == 'create':
        body = _build_body(input_file, name=name, description=description, zone_type=zone_type)
        tools.print_json(rest_crud.post(v4_endpoints.v4_endpoint('zones'), body))
        return

    # Remaining commands require zone_id
    if not zone_id:
        raise cli_exception.CliException('zone_id is required for ' + command)

    if command == 'get':
        tools.print_json(v4_client.v4_get('zones', zone_id))
        return

    if command == 'patch':
        body = _build_body(input_file, name=name, description=description, zone_type=zone_type)
        tools.print_json(v4_client.v4_replace('zones', zone_id, data=body))
        return

    if command == 'delete':
        result = v4_client.v4_delete('zones', zone_id)
        if result:
            tools.print_json(result)
        else:
            print('Zone deleted.')
        return


def _zone_list(extra_params=None):
    """List all zones. Zones are NOT workspace-scoped."""
    page_number = 0
    page_size = 200
    all_items = []
    while True:
        params = {'pageNumber': page_number, 'pageSize': page_size}
        if extra_params:
            params.update(extra_params)
        response = rest_crud.get(v4_endpoints.v4_endpoint('zones'), params)
        items = response.get('items', [])
        all_items.extend(items)
        total = response.get('total', 0)
        if len(all_items) >= total or not items:
            break
        page_number += 1
    return all_items


def _build_body(input_file, name=None, description=None, zone_type=None):
    """Build request body from file or named flags. Flags override file values."""
    body = {}
    if input_file:
        try:
            body = json.load(input_file)
        except json.JSONDecodeError as err:
            raise cli_exception.CliException(
                '%s\nThis command requires valid JSON input.' % str(err))
    if name is not None:
        body['name'] = name
    if description is not None:
        body['description'] = description
    if zone_type is not None:
        body['type'] = zone_type.upper()
    return body
