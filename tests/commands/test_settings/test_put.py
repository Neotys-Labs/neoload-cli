import pytest
from click.testing import CliRunner
from commands.test_settings import cli as settings
from commands.status import cli as status
from commands.logout import cli as logout
from helpers.test_utils import *


@pytest.mark.settings
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestPut:
    def test_minimal(self, monkeypatch, valid_data):
        runner = CliRunner()
        test_name = generate_test_settings_name()
        result_status = runner.invoke(status)
        assert 'settings id:' not in result_status.output

        mock_api_put(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id,
                     '{"id":"%s", "name":"%s", "description":"",'
                     '"scenarioName":"", "controllerZoneId":"defaultzone", '
                     '"lgZoneIds":{"defaultzone":1}, "testResultNamingPattern":""}' % (
                     valid_data.test_settings_id, test_name))
        result = runner.invoke(settings, ['put', valid_data.test_settings_id, '--rename', test_name])
        assert_success(result)
        json_result = json.loads(result.output)
        assert json_result['id'] == valid_data.test_settings_id
        # clear other fields
        assert json_result['name'] == test_name
        assert json_result['description'] == ''
        assert json_result['scenarioName'] == ''
        assert json_result['controllerZoneId'] == 'defaultzone'
        assert json_result['lgZoneIds'] == {"defaultzone": 1}
        assert json_result['testResultNamingPattern'] == ''

        result_status = runner.invoke(status)
        assert 'settings id: %s' % json_result['id'] in result_status.output

    def test_all_options(self, monkeypatch, valid_data):
        runner = CliRunner()
        test_name = generate_test_settings_name()
        mock_api_put(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id,
                     '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":"test description ",'
                     '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", '
                     '"lgZoneIds":{"defaultzone":5,"UdFyn":1}, "testResultNamingPattern":"test_${runID}"}' % test_name)
        result = runner.invoke(settings,
                               ['put', valid_data.test_settings_id, '--description', 'test description ',
                                '--scenario', 'scenario name', '--zone', 'defaultzone',
                                '--lgs', 'defaultzone:5,UdFyn:1', '--naming-pattern', 'test_${runID}',
                                '--rename', test_name])
        assert_success(result)
        json_result = json.loads(result.output)
        assert json_result['name'] == test_name
        assert json_result['description'] == 'test description '
        assert json_result['scenarioName'] == 'scenario name'
        assert json_result['controllerZoneId'] == 'defaultzone'
        assert json_result['lgZoneIds']['defaultzone'] == 5
        assert json_result['lgZoneIds']['UdFyn'] == 1
        assert json_result['testResultNamingPattern'] == 'test_${runID}'

    def test_input_map(self, monkeypatch, valid_data):
        runner = CliRunner()
        result_use = runner.invoke(settings, ['use', valid_data.test_settings_id])
        assert_success(result_use)

        test_name = generate_test_settings_name()
        mock_api_put(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id,
                     '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":"test description ",'
                     '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", '
                     '"lgZoneIds":{"defaultzone":5,"UdFyn":1}, "testResultNamingPattern":"test_${runID}"}' % test_name)
        result = runner.invoke(settings, ['put'],
                               input='{"name":"%s", "description":"test description ",'
                                     '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", '
                                     '"lgZoneIds":{"defaultzone":5,"UdFyn":1}, "testResultNamingPattern":"test_${runID}"}' % test_name)
        assert_success(result)
        json_result = json.loads(result.output)
        assert json_result['name'] == test_name
        assert json_result['description'] == 'test description '
        assert json_result['scenarioName'] == 'scenario name'
        assert json_result['controllerZoneId'] == 'defaultzone'
        assert json_result['lgZoneIds']['defaultzone'] == 5
        assert json_result['lgZoneIds']['UdFyn'] == 1
        assert json_result['testResultNamingPattern'] == 'test_${runID}'

    def test_default_fields(self, monkeypatch, valid_data):
        runner = CliRunner()
        if monkeypatch is None:
            # If mocks are disabled, call the real API to empty fields
            rest_crud.patch('v2/tests/%s' % valid_data.test_settings_id, {'controllerZoneId': '', 'lgZoneIds': {}})

        mock_api_put(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id,
                     '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "description":"test description ",'
                     '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", "lgZoneIds":{"defaultzone":1} }')
        result = runner.invoke(settings, ['put', valid_data.test_settings_id, '--description', 'test description ',
                                          '--rename', generate_test_settings_name()])
        assert_success(result)
        json_result = json.loads(result.output)
        print(result.output)
        assert json_result['description'] == 'test description '
        assert json_result['controllerZoneId'] == 'defaultzone'
        assert json_result['lgZoneIds']['defaultzone'] == 1

    def test_error_invalid_json(self, valid_data):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('bad.json', 'w') as f:
                f.write('{"key": not valid,,,}')
            result = runner.invoke(settings, ['--file', 'bad.json', 'put', valid_data.test_settings_id])
            assert result.exit_code == 1
            assert 'Error: Expecting value: line 1 column 9 (char 8)' in result.output
            assert 'This command requires a valid Json input' in result.output

    def test_error_not_logged_in(self):
        runner = CliRunner()
        result_logout = runner.invoke(logout)
        assert_success(result_logout)

        result = runner.invoke(settings, ['put', 'any'])
        assert result.exit_code == 1
        assert 'You are\'nt logged' in str(result.output)

    def test_not_found(self, monkeypatch, invalid_data):
        runner = CliRunner()
        mock_api_put(monkeypatch, 'v2/tests/%s' % invalid_data.uuid, '{"code":"404", "message": "Test not found."}')
        result = runner.invoke(settings, ['put', invalid_data.uuid], input='{"name":"any"}')
        assert 'Test not found' in result.output
        assert result.exit_code == 1
