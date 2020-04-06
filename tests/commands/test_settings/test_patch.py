import pytest
from click.testing import CliRunner
from commands.test_settings import cli as settings
from commands.status import cli as status
from commands.logout import cli as logout
from test_utils import *


@pytest.mark.test
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestPatch:
    def test_minimal(self, monkeypatch, valid_data):
        runner = CliRunner()
        result_status = runner.invoke(status)
        assert 'settings id:' not in result_status.output

        json_mock_before = '{"id":"%s", "name":"test-name before", "description":"test description ",' \
                           '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", ' \
                           '"lgZoneIds":{"defaultzone":5,"UdFyn":1}, "testResultNamingPattern":"test_${runId}"}' % valid_data.test_settings_id

        mock_api_get(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id, json_mock_before)
        result_ls = runner.invoke(settings, ['ls', valid_data.test_settings_id])
        assert_success(result_ls)
        json_test_before = json.loads(result_ls.output)

        mock_api_patch(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id, json_mock_before)
        result = runner.invoke(settings, ['patch', valid_data.test_settings_id], input='{}')
        assert_success(result)
        json_result = json.loads(result.output)
        assert json_result['id'] == valid_data.test_settings_id
        # leave other fields untouched
        assert json_result['name'] == json_test_before['name']
        assert json_result['description'] == json_test_before['description']
        assert json_result['scenarioName'] == json_test_before['scenarioName']
        assert json_result['controllerZoneId'] == json_test_before['controllerZoneId']
        assert json_result['lgZoneIds'] == json_test_before['lgZoneIds']
        assert json_result['testResultNamingPattern'] == json_test_before['testResultNamingPattern']

        result_status = runner.invoke(status)
        assert 'settings id: %s' % json_result['id'] in result_status.output


def test_all_options(self, monkeypatch, valid_data):
    runner = CliRunner()
    test_name = generate_test_settings_name()
    mock_api_patch(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id,
                   '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":"test description ",'
                   '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", '
                   '"lgZoneIds":{"defaultzone":5,"UdFyn":1}, "testResultNamingPattern":"test_${runId}"}' % test_name)
    result = runner.invoke(settings,
                           ['patch', valid_data.test_settings_id, '--description', 'test description ',
                            '--scenario', 'scenario name', '--controller-zone-id', 'defaultzone',
                            '--lg-zone-ids', 'defaultzone:5,UdFyn:1', '--naming-pattern', 'test_${runId}',
                            '--rename', test_name])
    assert_success(result)
    json_result = json.loads(result.output)
    assert json_result['name'] == test_name
    assert json_result['description'] == 'test description '
    assert json_result['scenarioName'] == 'scenario name'
    assert json_result['controllerZoneId'] == 'defaultzone'
    assert json_result['lgZoneIds']['defaultzone'] == 5
    assert json_result['lgZoneIds']['UdFyn'] == 1
    assert json_result['testResultNamingPattern'] == 'test_${runId}'


def test_input_map(self, monkeypatch, valid_data):
    runner = CliRunner()
    result_use = runner.invoke(settings, ['use', valid_data.test_settings_id])
    assert_success(result_use)

    test_name = generate_test_settings_name()
    mock_api_patch(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id,
                   '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":"test description ",'
                   '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", '
                   '"lgZoneIds":{"defaultzone":5,"UdFyn":1}, "testResultNamingPattern":"test_${runId}"}' % test_name)
    result = runner.invoke(settings, ['patch'],
                           input='{"name":"%s", "description":"test description ",'
                                 '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", '
                                 '"lgZoneIds":{"defaultzone":5,"UdFyn":1}, "testResultNamingPattern":"test_${runId}"}' % test_name)
    assert_success(result)
    json_result = json.loads(result.output)
    assert json_result['name'] == test_name
    assert json_result['description'] == 'test description '
    assert json_result['scenarioName'] == 'scenario name'
    assert json_result['controllerZoneId'] == 'defaultzone'
    assert json_result['lgZoneIds']['defaultzone'] == 5
    assert json_result['lgZoneIds']['UdFyn'] == 1
    assert json_result['testResultNamingPattern'] == 'test_${runId}'


def test_error_required(self):
    runner = CliRunner()
    result = runner.invoke(settings, ['patch'])
    assert result.exit_code == 1
    assert 'Error: Expecting value: line 1 column 1' in result.output
    assert 'This command requires a valid Json input' in result.output


def test_error_invalid_json(self):
    runner = CliRunner()
    result = runner.invoke(settings, ['patch'], input='{"key": not valid,,,}')
    assert result.exit_code == 1
    assert 'Error: Expecting value: line 1 column 9 (char 8)' in result.output
    assert 'This command requires a valid Json input' in result.output


def test_error_not_logged_in(self):
    runner = CliRunner()
    result_logout = runner.invoke(logout)
    assert_success(result_logout)

    result = runner.invoke(settings, ['patch', 'any'])
    assert result.exit_code == 1
    assert 'You are\'nt logged' in str(result.exception)


def test_not_found(self, monkeypatch, invalid_data):
    runner = CliRunner()
    mock_api_patch(monkeypatch, 'v2/tests/%s' % invalid_data.uuid, '{"code":"404", "message": "Test not found."}')
    result = runner.invoke(settings, ['patch', invalid_data.uuid], input='{}')
    assert 'Test not found' in result.output
    assert result.exit_code == 1
