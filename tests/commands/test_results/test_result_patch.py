import re

import pytest
from click.testing import CliRunner
from commands.test_results import cli as results
from commands.status import cli as status
from commands.logout import cli as logout
from helpers.test_utils import *


@pytest.mark.test
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestResultPatch:
    def test_minimal(self, monkeypatch, valid_data):
        runner = CliRunner()
        result_status = runner.invoke(status)
        assert 'settings id:' not in result_status.output

        mock_api_get(monkeypatch, 'v2/test-results/%s' % valid_data.test_settings_id,
                     '{"id":"%s", "name":"test-name before", "description":"test description ",'
                     '"quality-status":"PASSED"}' % valid_data.test_settings_id)
        result_ls = runner.invoke(results, ['ls', valid_data.test_settings_id])
        assert_success(result_ls)

        mock_api_put(monkeypatch, 'v2/test-results/%s' % valid_data.test_settings_id,
                     '{"id":"%s", "name":"test-name before", "description":"test description",'
                     '"quality-status":"PASSED"}' % valid_data.test_settings_id)
        result = runner.invoke(results, ['patch', valid_data.test_settings_id], input='{}')
        assert_success(result)
        json_result = json.loads(result.output)
        assert json_result['id'] == valid_data.test_settings_id
        # keep other fields
        assert json_result['name'] == 'test-name before'
        assert json_result['description'] == 'test description'
        assert json_result['quality-status'] == 'PASSED'

        result_status = runner.invoke(status)
        assert 'result id: %s' % json_result['id'] in result_status.output

    def test_all_options(self, monkeypatch, valid_data):
        runner = CliRunner()
        test_name = generate_test_settings_name()
        mock_api_put(monkeypatch, 'v2/test-results/%s' % valid_data.test_settings_id,
                     '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":"test description patch ",'
                     '"quality-status":"FAILED"}' % test_name)
        result = runner.invoke(results,
                               ['patch', valid_data.test_settings_id, '--description', 'test description patch ',
                                '--quality-status', 'FAILED', '--rename', test_name])
        assert_success(result)
        json_result = json.loads(result.output)
        assert json_result['name'] == test_name
        assert json_result['description'] == 'test description patch '
        assert json_result['quality-status'] == 'FAILED'

    def test_input_map(self, monkeypatch, valid_data):
        runner = CliRunner()
        result_use = runner.invoke(results, ['use', valid_data.test_settings_id])
        assert_success(result_use)

        test_name = generate_test_settings_name()
        mock_api_put(monkeypatch, 'v2/test-results/%s' % valid_data.test_settings_id,
                     '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":"test description ",'
                     '"quality-status":"test_${runId}"}' % test_name)
        result = runner.invoke(results, ['patch'],
                               input='{"name":"%s", "description":"test description ",'
                                     '"quality-status":"test_${runId}"}' % test_name)
        assert_success(result)
        json_result = json.loads(result.output)
        assert json_result['name'] == test_name
        assert json_result['description'] == 'test description '
        assert json_result['quality-status'] == 'test_${runId}'

    def test_error_required(self):
        runner = CliRunner()
        result = runner.invoke(results, ['patch'])
        assert result.exit_code == 1
        assert 'Error: Expecting value: line 1 column 1' in result.output
        assert 'This command requires a valid Json input' in result.output

    def test_error_invalid_json(self):
        runner = CliRunner()
        result = runner.invoke(results, ['patch'], input='{"key": not valid,,,}')
        assert result.exit_code == 1
        assert 'Error: Expecting value: line 1 column 9 (char 8)' in result.output
        assert 'This command requires a valid Json input' in result.output

    def test_error_not_logged_in(self):
        runner = CliRunner()
        result_logout = runner.invoke(logout)
        assert_success(result_logout)

        result = runner.invoke(results, ['patch', 'any'])
        assert result.exit_code == 1
        assert 'You are\'nt logged' in str(result.exception)

    def test_not_found(self, monkeypatch, invalid_data):
        runner = CliRunner()
        mock_api_put(monkeypatch, 'v2/test-results/%s' % invalid_data.uuid,
                     '{"code":"404", "message": "Test result not found."}')
        result = runner.invoke(results, ['patch', invalid_data.uuid], input='{}')
        assert 'Test result not found' in result.output
        assert result.exit_code == 1

    def test_wrong_quality_status(self):
        runner = CliRunner()
        result = runner.invoke(results, ['patch', '--quality-status', 'not_valid_quality'])
        assert result.exit_code == 2
        assert re.compile(".*Error: Invalid value for [\"']--quality-status[\"']: invalid choice: not_valid_quality."
                          " \(choose from PASSED, FAILED\).*", re.DOTALL).match(result.output) is not None
