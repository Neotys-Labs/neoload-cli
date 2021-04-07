import pytest
from click.testing import CliRunner
from commands.test_settings import cli as settings
from commands.status import cli as status
from commands.logout import cli as logout
from tests.helpers.test_utils import *


@pytest.mark.settings
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestPatch:
    def test_minimal(self, monkeypatch, valid_data):
        runner = CliRunner()
        result_status = runner.invoke(status)
        assert 'settings id:' not in result_status.output

        json_mock_before = '{"id":"%s", "name":"test-name before", "description":"test description ",' \
                           '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", ' \
                           '"lgZoneIds":{"defaultzone":5,"UdFyn":1}, "testResultNamingPattern":"test_${runID}"}' % valid_data.test_settings_id

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
        assert json_result['controllerZoneId'] == json_test_before['controllerZoneId'] or (
                json_test_before['controllerZoneId'] == '' and json_result['controllerZoneId'] == 'defaultzone')
        assert json_result['lgZoneIds'] == json_test_before['lgZoneIds'] or (
                json_test_before['lgZoneIds'] == {} and json_result['lgZoneIds'] == {'defaultzone': 1})
        assert json_result['testResultNamingPattern'] == json_test_before['testResultNamingPattern']

        result_status = runner.invoke(status)
        assert 'settings id: %s' % json_result['id'] in result_status.output

    def test_all_options(self, monkeypatch, valid_data):
        runner = CliRunner()
        test_name = generate_test_settings_name()
        mock_api_patch(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id,
                       '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":"test description ",'
                       '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", '
                       '"lgZoneIds":{"defaultzone":5,"UdFyn":1}, "testResultNamingPattern":"test_${runID}"}' % test_name)
        result = runner.invoke(settings,
                               ['patch', valid_data.test_settings_id, '--description', 'test description ',
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

    def test_default_fields(self, monkeypatch, valid_data):
        runner = CliRunner()
        if monkeypatch is None:
            # If mocks are disabled, call the real API to empty fields
            rest_crud.patch('v2/tests/%s' % valid_data.test_settings_id, {'controllerZoneId': '', 'lgZoneIds': {}})

        mock_api_patch(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id,
                       '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "description":"test description ",'
                       '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", "lgZoneIds":{"defaultzone":1} }')
        result = runner.invoke(settings, ['patch', valid_data.test_settings_id,
                                          '--rename', generate_test_settings_name()])
        assert_success(result)
        json_result = json.loads(result.output)
        print(result.output)
        assert json_result['controllerZoneId'] == 'defaultzone'
        assert json_result['lgZoneIds']['defaultzone'] == 1

    def test_lgs(self, monkeypatch, valid_data):
        runner = CliRunner()
        if monkeypatch is None:
            # If mocks are disabled, call the real API to empty fields
            rest_crud.patch('v2/tests/%s' % valid_data.test_settings_id, {'controllerZoneId': '', 'lgZoneIds': {}})

        mock_api_patch(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id,
                       '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "description":"test description ",'
                       '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", "lgZoneIds":{"defaultzone":4} }')
        result = runner.invoke(settings, ['patch', valid_data.test_settings_id, '--lgs', '4'])
        assert_success(result)
        json_result = json.loads(result.output)
        print(result.output)
        assert json_result['controllerZoneId'] == 'defaultzone'
        assert json_result['lgZoneIds']['defaultzone'] == 4

    def test_lgs_and_zone(self, monkeypatch, valid_data):
        runner = CliRunner()
        if monkeypatch is None:
            # If mocks are disabled, call the real API to empty fields
            rest_crud.patch('v2/tests/%s' % valid_data.test_settings_id, {'controllerZoneId': '', 'lgZoneIds': {}})

        mock_api_patch(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id,
                       '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "description":"test description ",'
                       '"scenarioName":"scenario name", "controllerZoneId":"some_zone_id", "lgZoneIds":{"some_zone_id":65} }')
        result = runner.invoke(settings, ['patch', valid_data.test_settings_id, '--zone', 'some_zone_id', '--lgs', '65'])
        assert_success(result)
        json_result = json.loads(result.output)
        print(result.output)
        assert json_result['controllerZoneId'] == 'some_zone_id'
        assert json_result['lgZoneIds']['some_zone_id'] == 65

    def test_input_map(self, monkeypatch, valid_data):
        runner = CliRunner()
        result_use = runner.invoke(settings, ['use', valid_data.test_settings_id])
        assert_success(result_use)

        test_name = generate_test_settings_name()
        mock_api_patch(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id,
                       '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":"test description ",'
                       '"scenarioName":"scenario name", "controllerZoneId":"defaultzone", '
                       '"lgZoneIds":{"defaultzone":5,"UdFyn":1}, "testResultNamingPattern":"test_${runID}"}' % test_name)
        result = runner.invoke(settings, ['patch'],
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


    def test_error_invalid_json(self,valid_data):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('bad.json', 'w') as f:
                f.write('{"key": not valid,,,}')
            result = runner.invoke(settings, ['patch', '--file', 'bad.json', valid_data.test_settings_id])
            assert result.exit_code == 1
            assert 'Error: Expecting value: line 1 column 9 (char 8)' in result.output
            assert 'This command requires a valid Json input' in result.output

    def test_error_not_logged_in(self):
        runner = CliRunner()
        result_logout = runner.invoke(logout)
        assert_success(result_logout)

        result = runner.invoke(settings, ['patch', 'any'])
        assert result.exit_code == 1
        assert 'You aren\'t logged' in str(result.output)

    def test_not_found(self, monkeypatch, invalid_data):
        runner = CliRunner()
        mock_api_patch(monkeypatch, 'v2/tests/%s' % invalid_data.uuid, '{"code":"404", "message": "Test not found."}')
        result = runner.invoke(settings, ['patch', invalid_data.uuid], input='{}')
        assert 'Test not found' in result.output
        assert result.exit_code == 1
