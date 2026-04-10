import json
import pytest
from unittest.mock import MagicMock
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud, user_data
from neoload_cli_lib.v4 import v4_client, v4_endpoints
import commands.v4_test_executions as v4_te_module
from commands.v4_test_executions import cli


def _make_response(status_code, content=b''):
    """Create a mock requests.Response."""
    response = Response()
    response.status_code = status_code
    response._content = content
    return response


@pytest.mark.usefixtures("neoload_login")
class TestV4TestExecutions:
    def test_missing_command(self, monkeypatch):
        """Invoking without a command should print help message."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_create_no_wait(self, monkeypatch):
        """create without --wait: posts body and returns execution JSON."""
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'post',
                            lambda endpoint, data: {'id': 'exec-1', 'step': 'INITIALIZING'})
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--test-id', 'abc'])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['id'] == 'exec-1'

    def test_create_with_scenario_flag(self, monkeypatch):
        """create --scenario: body must contain 'scenarioName' field (per D-03)."""
        if monkeypatch is None:
            return
        captured = {}

        def mock_post(endpoint, data):
            captured['data'] = data
            return {'id': 'exec-1', 'step': 'INITIALIZING'}

        monkeypatch.setattr(rest_crud, 'post', mock_post)
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--test-id', 'abc', '--scenario', 'myScenario'])
        assert result.exit_code == 0
        assert captured['data']['scenarioName'] == 'myScenario'

    def test_create_with_zone_type_flag(self, monkeypatch):
        """create --zone-type: body must contain 'zoneType' field (per D-03)."""
        if monkeypatch is None:
            return
        captured = {}

        def mock_post(endpoint, data):
            captured['data'] = data
            return {'id': 'exec-1', 'step': 'INITIALIZING'}

        monkeypatch.setattr(rest_crud, 'post', mock_post)
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--test-id', 'abc', '--zone-type', 'CLOUD'])
        assert result.exit_code == 0
        assert captured['data']['zoneType'] == 'CLOUD'

    def test_create_with_wait_passed(self, monkeypatch):
        """create --wait with STARTED_TEST terminal step: exits 0 (non-failure terminal)."""
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'post',
                            lambda endpoint, data: {'id': 'exec-1', 'step': 'INITIALIZING'})
        # v4_get returns terminal step on first call (STARTED_TEST is terminal but not FAIL)
        monkeypatch.setattr(v4_client, 'v4_get',
                            lambda *args: {'id': 'exec-1', 'step': 'STARTED_TEST'})
        monkeypatch.setattr(v4_te_module, 'POLL_INTERVAL_SECONDS', 0)
        monkeypatch.setattr(v4_te_module.time, 'sleep', lambda x: None)
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--test-id', 'abc', '--wait'])
        assert result.exit_code == 0

    def test_create_with_wait_failed(self, monkeypatch):
        """create --wait with FAILED terminal step: exits 1 per D-05."""
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'post',
                            lambda endpoint, data: {'id': 'exec-1', 'step': 'INITIALIZING'})
        monkeypatch.setattr(v4_client, 'v4_get',
                            lambda *args: {'id': 'exec-1', 'step': 'FAILED'})
        monkeypatch.setattr(v4_te_module.time, 'sleep', lambda x: None)
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--test-id', 'abc', '--wait'])
        assert result.exit_code == 1

    def test_create_with_wait_cancelled(self, monkeypatch):
        """create --wait with CANCELLED step: exits 1 per D-05 (CANCELLED = TERMINATED equivalent)."""
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'post',
                            lambda endpoint, data: {'id': 'exec-1', 'step': 'INITIALIZING'})
        monkeypatch.setattr(v4_client, 'v4_get',
                            lambda *args: {'id': 'exec-1', 'step': 'CANCELLED'})
        monkeypatch.setattr(v4_te_module.time, 'sleep', lambda x: None)
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--test-id', 'abc', '--wait'])
        # CANCELLED exits 1 per D-05 (user-confirmed CANCELLED = TERMINATED equivalent)
        assert result.exit_code == 1

    def test_get(self, monkeypatch):
        """get <id>: calls v4_get and returns execution JSON."""
        if monkeypatch is None:
            return
        monkeypatch.setattr(v4_client, 'v4_get',
                            lambda *args: {'id': 'exec-id', 'step': 'STARTED_TEST'})
        runner = CliRunner()
        result = runner.invoke(cli, ['get', 'exec-id'])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['id'] == 'exec-id'

    def test_cancel(self, monkeypatch):
        """cancel <id>: calls rest_crud.delete and prints confirmation on 202 empty body."""
        if monkeypatch is None:
            return
        mock_response = _make_response(202, b'')
        monkeypatch.setattr(rest_crud, 'delete', lambda endpoint: mock_response)
        runner = CliRunner()
        result = runner.invoke(cli, ['cancel', 'exec-id'])
        assert result.exit_code == 0
        assert 'cancel requested' in result.output.lower()

    def test_force_cancel(self, monkeypatch):
        """force-cancel <id>: calls rest_crud.delete with /forced endpoint."""
        if monkeypatch is None:
            return
        captured = {}

        def mock_delete(endpoint):
            captured['endpoint'] = endpoint
            return _make_response(202, b'')

        monkeypatch.setattr(rest_crud, 'delete', mock_delete)
        runner = CliRunner()
        result = runner.invoke(cli, ['force-cancel', 'exec-id'])
        assert result.exit_code == 0
        assert 'cancel requested' in result.output.lower()
        assert 'forced' in captured['endpoint']

    def test_logs(self, monkeypatch):
        """logs <resultId>: polls /v4/results/{id}/logs and prints log entries."""
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'get',
                            lambda endpoint, params=None: {
                                'items': [{'date': '2024-01-01', 'level': 'INFO', 'line': 'Test started'}],
                                'total': 1, 'pageNumber': 0, 'pageSize': 200
                            })
        monkeypatch.setattr(v4_te_module.time, 'sleep', lambda x: None)
        runner = CliRunner()
        result = runner.invoke(cli, ['logs', 'result-id-123'])
        assert result.exit_code == 0
        assert 'Test started' in result.output

    def test_create_missing_test_id(self, monkeypatch):
        """create without --test-id: posts with empty body (pass-through; API validates)."""
        if monkeypatch is None:
            return
        captured = {}

        def mock_post(endpoint, data):
            captured['data'] = data
            return {'id': 'exec-1', 'step': 'INITIALIZING'}

        monkeypatch.setattr(rest_crud, 'post', mock_post)
        runner = CliRunner()
        result = runner.invoke(cli, ['create'])
        assert result.exit_code == 0
        # No testId was passed, so it's not in the body
        assert 'testId' not in captured.get('data', {})

    def test_get_missing_id(self, monkeypatch):
        """get without an id: raises CliException."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['get'])
        # CliException results in non-zero exit or error message
        assert result.exit_code != 0 or 'id is required' in result.output

    def test_cancel_missing_id(self, monkeypatch):
        """cancel without an id: raises CliException."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['cancel'])
        assert result.exit_code != 0 or 'id is required' in result.output

    def test_logs_endpoint_uses_results_path(self, monkeypatch):
        """logs subcommand: endpoint must be /v4/results/{id}/logs (not test-executions)."""
        if monkeypatch is None:
            return
        captured = {}

        def mock_get(endpoint, params=None):
            captured['endpoint'] = endpoint
            return {'items': [], 'total': 0, 'pageNumber': 0, 'pageSize': 200}

        monkeypatch.setattr(rest_crud, 'get', mock_get)
        monkeypatch.setattr(v4_te_module.time, 'sleep', lambda x: None)
        runner = CliRunner()
        result = runner.invoke(cli, ['logs', 'my-result-id'])
        assert result.exit_code == 0
        assert 'results' in captured.get('endpoint', '')
        assert 'my-result-id' in captured.get('endpoint', '')
        assert 'logs' in captured.get('endpoint', '')

    def test_create_with_wait_no_exec_id(self, monkeypatch):
        """create --wait: raises CliException when no id is in the response (line 55)."""
        if monkeypatch is None:
            return
        # API returns response without 'id' key
        monkeypatch.setattr(rest_crud, 'post',
                            lambda endpoint, data: {'step': 'INITIALIZING'})
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--test-id', 'abc', '--wait'])
        assert result.exit_code != 0

    def test_cancel_with_body_response(self, monkeypatch):
        """cancel <id>: when response has content, prints JSON body (line 73)."""
        if monkeypatch is None:
            return
        body = json.dumps({'status': 'cancelling'}).encode()
        mock_response = _make_response(202, body)
        monkeypatch.setattr(rest_crud, 'delete', lambda endpoint: mock_response)
        runner = CliRunner()
        result = runner.invoke(cli, ['cancel', 'exec-id'])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['status'] == 'cancelling'

    def test_force_cancel_missing_id(self, monkeypatch):
        """force-cancel without an id: raises CliException (line 80)."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['force-cancel'])
        assert result.exit_code != 0

    def test_force_cancel_with_body_response(self, monkeypatch):
        """force-cancel <id>: when response has content, prints JSON body (line 83)."""
        if monkeypatch is None:
            return
        body = json.dumps({'status': 'force-cancelling'}).encode()
        mock_response = _make_response(202, body)
        monkeypatch.setattr(rest_crud, 'delete', lambda endpoint: mock_response)
        runner = CliRunner()
        result = runner.invoke(cli, ['force-cancel', 'exec-id'])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['status'] == 'force-cancelling'

    def test_logs_missing_id(self, monkeypatch):
        """logs without an id: raises CliException (line 90)."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['logs'])
        assert result.exit_code != 0

    def test_create_invalid_json_file(self, monkeypatch):
        """create --file with invalid JSON: raises CliException (lines 101-104)."""
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'post',
                            lambda endpoint, data: {'id': 'exec-1'})
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--file', '-'], input='not valid json{{{')
        assert result.exit_code != 0

    def test_create_with_all_flags(self, monkeypatch):
        """create with all optional flags: all fields in body (lines 109/111/117/119/121/123)."""
        if monkeypatch is None:
            return
        captured = {}

        def mock_post(endpoint, data):
            captured['data'] = data
            return {'id': 'exec-1', 'step': 'INITIALIZING'}

        monkeypatch.setattr(rest_crud, 'post', mock_post)
        runner = CliRunner()
        result = runner.invoke(cli, [
            'create',
            '--test-id', 'tid-1',
            '--name', 'my-exec',
            '--description', 'a description',
            '--scenario', 'sc1',
            '--zone-type', 'CLOUD',
            '--web-vu', '10',
            '--sap-vu', '5',
            '--duration', '3600',
            '--reservation-id', 'res-abc',
        ])
        assert result.exit_code == 0
        d = captured['data']
        assert d['testId'] == 'tid-1'
        assert d['name'] == 'my-exec'
        assert d['description'] == 'a description'
        assert d['scenarioName'] == 'sc1'
        assert d['zoneType'] == 'CLOUD'
        assert d['webVu'] == 10
        assert d['sapVu'] == 5
        assert d['duration'] == 3600
        assert d['reservationId'] == 'res-abc'

    def test_wait_for_completion_polls_until_terminal(self, monkeypatch):
        """_wait_for_completion: polls (sleeps) until terminal step, hitting line 139."""
        if monkeypatch is None:
            return
        call_count = {'n': 0}

        def mock_v4_get(*args):
            call_count['n'] += 1
            if call_count['n'] < 3:
                return {'id': 'exec-1', 'step': 'INITIALIZING'}
            return {'id': 'exec-1', 'step': 'STARTED_TEST'}

        sleep_calls = []
        monkeypatch.setattr(rest_crud, 'post',
                            lambda endpoint, data: {'id': 'exec-1', 'step': 'INITIALIZING'})
        monkeypatch.setattr(v4_client, 'v4_get', mock_v4_get)
        monkeypatch.setattr(v4_te_module.time, 'sleep', lambda x: sleep_calls.append(x))
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--test-id', 'abc', '--wait'])
        assert result.exit_code == 0
        # Should have slept at least once before reaching terminal step
        assert len(sleep_calls) >= 1

    def test_logs_multiple_pages(self, monkeypatch):
        """_poll_logs: fetches page 0, then page 1 when total > first page (lines 161-162)."""
        if monkeypatch is None:
            return
        call_count = {'n': 0}

        def mock_get(endpoint, params=None):
            call_count['n'] += 1
            if call_count['n'] == 1:
                return {
                    'items': [{'date': '2024-01-01', 'level': 'INFO', 'line': 'msg1'}],
                    'total': 2,
                }
            # Second page: returns remaining item, total_fetched catches up
            return {
                'items': [{'date': '2024-01-01', 'level': 'INFO', 'line': 'msg2'}],
                'total': 2,
            }

        monkeypatch.setattr(rest_crud, 'get', mock_get)
        monkeypatch.setattr(v4_te_module.time, 'sleep', lambda x: None)
        runner = CliRunner()
        result = runner.invoke(cli, ['logs', 'result-multi'])
        assert result.exit_code == 0
        assert 'msg1' in result.output
        assert 'msg2' in result.output
        assert call_count['n'] == 2
