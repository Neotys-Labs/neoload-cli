import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_client, v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'ls', 'create', 'get', 'patch', 'delete', 'scenario-get', 'scenario-update'
], case_sensitive=False), required=False)
@click.argument('id', type=str, required=False)
@click.argument('scenario_name', type=str, required=False)
@click.option('--name', help='Test name')
@click.option('--description', help='Test description')
@click.option('--scenario', help='Scenario name')
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file')
@click.option('--delete-results', is_flag=True, default=False, help='Also delete associated results')
def cli(command, id, scenario_name, name, description, scenario, input_file, delete_results):
    """
    ls              # List all tests in the current workspace                   .
    create          # Create a new test                                         .
    get             # Get a test by ID                                          .
    patch           # Update fields of a test by ID                            .
    delete          # Delete a test by ID                                       .
    scenario-get    # Get a scenario from a test                                .
    scenario-update # Update a scenario in a test                               .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-tests --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'ls':
        tools.print_json(v4_client.v4_list('tests'))

    elif command == 'create':
        body = _build_body(input_file, name=name, description=description, scenario=scenario)
        tools.print_json(v4_client.v4_create('tests', data=body))

    elif command == 'get':
        if not id:
            raise cli_exception.CliException('id is required for get')
        tools.print_json(v4_client.v4_get('tests', id))

    elif command == 'patch':
        if not id:
            raise cli_exception.CliException('id is required for patch')
        body = _build_body(input_file, name=name, description=description, scenario=scenario)
        tools.print_json(v4_client.v4_update('tests', id, data=body))

    elif command == 'delete':
        if not id:
            raise cli_exception.CliException('id is required for delete')
        if delete_results:
            endpoint = v4_endpoints.v4_endpoint('tests', id) + '?deleteResults=true'
            response = rest_crud.delete(endpoint)
            if response.status_code == 204 or not response.content:
                print('Test deleted.')
            else:
                tools.print_json(response.json())
        else:
            result = v4_client.v4_delete('tests', id)
            if result:
                tools.print_json(result)
            else:
                print('Test deleted.')

    elif command == 'scenario-get':
        if not id:
            raise cli_exception.CliException('test_id is required for scenario-get')
        if not scenario_name:
            raise cli_exception.CliException('scenario_name is required for scenario-get')
        tools.print_json(v4_client.v4_get('tests', id, 'scenarios', scenario_name))

    elif command == 'scenario-update':
        if not id:
            raise cli_exception.CliException('test_id is required for scenario-update')
        if not scenario_name:
            raise cli_exception.CliException('scenario_name is required for scenario-update')
        if not input_file:
            raise cli_exception.CliException('--file is required for scenario-update')
        body = json.load(input_file)
        tools.print_json(v4_client.v4_replace('tests', id, 'scenarios', scenario_name, data=body))


def _build_body(input_file, name=None, description=None, scenario=None):
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
    if scenario is not None:
        body['scenarioName'] = scenario
    return body
