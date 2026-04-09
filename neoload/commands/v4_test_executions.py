import json
import sys
import time
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_client, v4_endpoints

# Terminal steps from GetTestExecutionResponse.step enum
TERMINAL_STEPS = {'FAILED', 'CANCELLED', 'FAILED_TO_PREPARE_CONTROLLER',
                  'FAILED_TO_PREPARE_LGS', 'STARTED_TEST'}
# Steps that indicate failure -> exit 1
# User-confirmed mapping (per D-05): CANCELLED is the v4 API equivalent of TERMINATED.
# FAIL_EXIT_STEPS = {'FAILED', 'CANCELLED'} is the definitive set.
FAIL_EXIT_STEPS = {'FAILED', 'CANCELLED'}
POLL_INTERVAL_SECONDS = 5
LOG_POLL_INTERVAL_SECONDS = 2


@click.command()
@click.argument('command', type=click.Choice([
    'create', 'get', 'cancel', 'force-cancel', 'logs'
], case_sensitive=False), required=False)
@click.argument('id', type=str, required=False)
@click.option('--test-id', help='Test ID to execute')
@click.option('--name', help='Execution name')
@click.option('--description', help='Execution description')
@click.option('--scenario', help='Scenario name (writes body field scenarioName)')
@click.option('--zone-type', help='Zone type (writes body field zoneType)')
@click.option('--web-vu', type=int, help='Number of web virtual users')
@click.option('--sap-vu', type=int, help='Number of SAP virtual users')
@click.option('--duration', type=int, help='Duration in seconds')
@click.option('--reservation-id', help='Reservation ID')
@click.option('--wait', 'wait_completion', is_flag=True, default=False,
              help='Wait for execution to reach terminal status')
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file')
def cli(command, id, test_id, name, description, scenario, zone_type, web_vu, sap_vu,
        duration, reservation_id, wait_completion, input_file):
    """v4-test-executions: create, get, cancel, force-cancel, logs"""
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-test-executions --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'create':
        body = _build_body(input_file, test_id=test_id, name=name,
                           description=description, scenario=scenario,
                           zone_type=zone_type, web_vu=web_vu, sap_vu=sap_vu,
                           duration=duration, reservation_id=reservation_id)
        # test-executions create does NOT use v4_create (no workspaceId injection)
        result = rest_crud.post(v4_endpoints.v4_endpoint('test-executions'), body)
        if wait_completion:
            execution_id = result.get('id')
            if not execution_id:
                raise cli_exception.CliException('No execution ID returned from create')
            _wait_for_completion(execution_id)
        else:
            tools.print_json(result)
        return

    if command == 'get':
        if not id:
            raise cli_exception.CliException('id is required for get')
        tools.print_json(v4_client.v4_get('test-executions', id))
        return

    if command == 'cancel':
        if not id:
            raise cli_exception.CliException('id is required for cancel')
        response = rest_crud.delete(v4_endpoints.v4_endpoint('test-executions', id))
        # cancel returns 202 with empty body
        if response.content:
            tools.print_json(response.json())
        else:
            print('Test execution cancel requested.')
        return

    if command == 'force-cancel':
        if not id:
            raise cli_exception.CliException('id is required for force-cancel')
        response = rest_crud.delete(v4_endpoints.v4_endpoint('test-executions', id, 'forced'))
        if response.content:
            tools.print_json(response.json())
        else:
            print('Test execution force-cancel requested.')
        return

    if command == 'logs':
        if not id:
            raise cli_exception.CliException('result_id is required for logs')
        _poll_logs(id)
        return


def _build_body(input_file, test_id=None, name=None, description=None,
                scenario=None, zone_type=None, web_vu=None, sap_vu=None,
                duration=None, reservation_id=None):
    """Build the request body for create from file and/or named flags."""
    body = {}
    if input_file:
        try:
            body = json.load(input_file)
        except json.JSONDecodeError as err:
            raise cli_exception.CliException(
                '%s\nThis command requires valid JSON input.' % str(err))
    if test_id is not None:
        body['testId'] = test_id
    if name is not None:
        body['name'] = name
    if description is not None:
        body['description'] = description
    if scenario is not None:
        body['scenarioName'] = scenario
    if zone_type is not None:
        body['zoneType'] = zone_type
    if web_vu is not None:
        body['webVu'] = web_vu
    if sap_vu is not None:
        body['sapVu'] = sap_vu
    if duration is not None:
        body['duration'] = duration
    if reservation_id is not None:
        body['reservationId'] = reservation_id
    return body


def _wait_for_completion(execution_id):
    """Poll GET /v4/test-executions/{id} until a terminal step is reached."""
    while True:
        result = v4_client.v4_get('test-executions', execution_id)
        step = result.get('step', '')
        tools.print_json(result)  # print current status on each poll
        if step in TERMINAL_STEPS:
            # User-confirmed mapping (D-05): CANCELLED = TERMINATED equivalent.
            # FAIL_EXIT_STEPS = {'FAILED', 'CANCELLED'} exits with code 1.
            if step in FAIL_EXIT_STEPS:
                sys.exit(1)
            return
        time.sleep(POLL_INTERVAL_SECONDS)


def _poll_logs(result_id):
    """Poll GET /v4/results/{resultId}/logs until all log entries are fetched."""
    page_number = 0
    total_fetched = 0
    while True:
        response = rest_crud.get(
            v4_endpoints.v4_endpoint('results', result_id, 'logs'),
            {'pageNumber': page_number, 'pageSize': 200}
        )
        items = response.get('items', [])
        total = response.get('total', 0)
        for entry in items:
            date = entry.get('date', '')
            level = entry.get('level', '')
            line = entry.get('line', '')
            print('%s %s %s' % (date, level, line))
        total_fetched += len(items)
        if total_fetched >= total or not items:
            break
        page_number += 1
        time.sleep(LOG_POLL_INTERVAL_SECONDS)
