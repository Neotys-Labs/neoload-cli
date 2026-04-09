import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_client, v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'ls', 'get', 'patch', 'delete',
    'contexts', 'elements', 'monitors', 'statistics', 'timeseries',
    'search-criteria'
], case_sensitive=False), required=False)
@click.argument('id', type=str, required=False)
@click.option('--name', help='Result name')
@click.option('--description', help='Result description')
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file')
def cli(command, id, name, description, input_file):
    """
    ls               # List test results for the current workspace          .
    get              # Get a single test result by ID                       .
    patch            # Patch a test result (name, description, or --file)  .
    delete           # Delete a test result by ID                          .
    contexts         # Get result contexts by result ID                    .
    elements         # Get result elements by result ID                    .
    monitors         # Get result monitors by result ID                    .
    statistics       # Get result statistics by result ID                  .
    timeseries       # Get result timeseries by result ID                  .
    search-criteria  # Get search criteria for the current workspace       .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-results --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'ls':
        tools.print_json(v4_client.v4_list('results'))
        return

    if command == 'search-criteria':
        # search-criteria is workspace-scoped but NOT paginated — use rest_crud.get directly
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('results', 'search-criteria'),
            v4_endpoints.v4_workspace_params()
        ))
        return

    # All remaining commands require an id
    if not id:
        raise cli_exception.CliException('id is required for ' + command)

    if command == 'get':
        tools.print_json(v4_client.v4_get('results', id))
    elif command == 'patch':
        body = _build_body(input_file, name=name, description=description)
        tools.print_json(v4_client.v4_update('results', id, data=body))
    elif command == 'delete':
        result = v4_client.v4_delete('results', id)
        if result:
            tools.print_json(result)
        else:
            print('Result deleted.')
    elif command in ('contexts', 'elements', 'monitors', 'statistics', 'timeseries'):
        tools.print_json(v4_client.v4_get('results', id, command))


def _build_body(input_file, name=None, description=None):
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
    return body
