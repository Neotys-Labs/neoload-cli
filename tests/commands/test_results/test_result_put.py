import re

import pytest
from click.testing import CliRunner
from commands.test_results import cli as results
from commands.status import cli as status
from commands.logout import cli as logout
from tests.helpers.test_utils import *


@pytest.mark.results
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestResultPut:
    def test_minimal(self, monkeypatch, valid_data):
        runner = CliRunner()
        result_status = runner.invoke(status)
        assert 'result id:' not in result_status.output

        mock_api_get(monkeypatch, 'v2/test-results/%s' % valid_data.test_result_id,
                     '{"id":"%s", "name":"test-name before", "description":"", "qualityStatus":"PASSED",'
                     '"externalUrl":"http://urlBefore","externalUrlLabel":"libBefore"}' % valid_data.test_result_id)
        result_ls = runner.invoke(results, ['ls', valid_data.test_result_id])
        assert_success(result_ls)
        json_before = json.loads(result_ls.output)

        mock_api_put(monkeypatch, 'v2/test-results/%s' % valid_data.test_result_id,
                     '{"id":"%s", "name":"test-name before", "description":"", "qualityStatus":"PASSED",'
                     '"externalUrl":"","externalUrlLabel":""}' % valid_data.test_result_id)
        result = runner.invoke(results, ['put', valid_data.test_result_id],
                               input='{"name":"%s", "qualityStatus":"%s"}' % (
                                   json_before['name'], json_before['qualityStatus']))
        assert_success(result)
        json_result = json.loads(result.output)
        assert json_result['id'] == valid_data.test_result_id
        # keep other fields
        assert json_result['name'] == json_before['name']
        assert json_result['description'] == ''
        assert json_result['qualityStatus'] == json_before['qualityStatus']
        assert json_result['externalUrl'] == ''
        assert json_result['externalUrlLabel'] == ''

        result_status = runner.invoke(status)
        assert 'result id: %s' % json_result['id'] in result_status.output

    def test_all_options(self, monkeypatch, valid_data):
        runner = CliRunner()
        test_name = generate_test_result_name()
        mock_api_put(monkeypatch, 'v2/test-results/%s' % valid_data.test_result_id,
                     '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":"test description put ",'
                     '"qualityStatus":"FAILED","externalUrl":"http://url","externalUrlLabel":"external_lib", "isLocked":"true"}' % test_name)
        result = runner.invoke(results,
                               ['put', valid_data.test_result_id, '--description', 'test description patch ',
                                '--quality-status', 'FAILED', '--rename', test_name, '--external-url', 'http://url',
                                '--external-url-label', 'external_lib' , '--lock']) 
        assert_success(result)
        json_result = json.loads(result.output)
        assert json_result['name'] == test_name
        assert json_result['description'] == 'test description put '
        assert json_result['qualityStatus'] == 'FAILED'
        assert json_result['externalUrl'] == 'http://url'
        assert json_result['externalUrlLabel'] == 'external_lib'
        assert json_result['isLocked'] == 'true'

    def test_input_map(self, monkeypatch, valid_data):
        runner = CliRunner()
        result_use = runner.invoke(results, ['use', valid_data.test_result_id])
        assert_success(result_use)

        test_name = generate_test_result_name()
        mock_api_put(monkeypatch, 'v2/test-results/%s' % valid_data.test_result_id,
                     '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":"test description ",'
                     '"qualityStatus":"PASSED","externalUrl":"http://url2","externalUrlLabel":"external_lib2", "isLocked":"true"}' % test_name)
        result = runner.invoke(results, ['put'], input='{"name":"%s", "description":"test description ",'
                                                       '"qualityStatus":"PASSED","externalUrl":"http://url2",'
                                                       '"externalUrlLabel":"external_lib2", "isLocked":"true"}' % test_name)
        assert_success(result)
        json_result = json.loads(result.output)
        assert json_result['name'] == test_name
        assert json_result['description'] == 'test description '
        assert json_result['qualityStatus'] == 'PASSED'
        assert json_result['externalUrl'] == 'http://url2'
        assert json_result['externalUrlLabel'] == 'external_lib2'
        assert json_result['isLocked'] == 'true'

    def test_error_invalid_json(self, valid_data):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('bad.json', 'w') as f:
                f.write('{"key": not valid,,,}')
            result = runner.invoke(results, ['--file', 'bad.json', 'put', valid_data.test_settings_id])
            assert result.exit_code == 1
            assert 'Error: Expecting value: line 1 column 9 (char 8)' in result.output
            assert 'This command requires a valid Json input' in result.output

    def test_error_not_logged_in(self):
        runner = CliRunner()
        result_logout = runner.invoke(logout)
        assert_success(result_logout)

        result = runner.invoke(results, ['put', 'any'])
        assert result.exit_code == 1
        assert 'You aren\'t logged' in str(result.output)

    def test_not_found(self, monkeypatch, invalid_data):
        runner = CliRunner()
        mock_api_put(monkeypatch, 'v2/test-results/%s' % invalid_data.uuid,
                     '{"code":"404", "message": "Test result not found."}')
        result = runner.invoke(results, ['put', invalid_data.uuid], input='{"qualityStatus":"PASSED"}')
        assert 'Test result not found' in result.output
        assert result.exit_code == 1

    def test_wrong_quality_status(self):
        runner = CliRunner()
        result = runner.invoke(results, ['put', '--quality-status', 'not_valid_quality'])
        assert result.exit_code == 2
        assert "Invalid value for '--quality-status': 'not_valid_quality' is not one of 'PASSED', 'FAILED'" in result.output
