import platform
import time

import pytest
from click.testing import CliRunner
from commands.test_settings import cli as settings
from commands.status import cli as status
from commands.logout import cli as logout
from tests.helpers.test_utils import *


@pytest.mark.settings
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestCreateOrPatch:
    test_name = 'test_name_Python' + str(platform.python_version()) + '_' + str(round(time.time() * 1000))

    @pytest.mark.makelivecalls
    def test_pre_conditions_clear_status(self):
        runner = CliRunner()
        result_logout = runner.invoke(logout)
        assert_success(result_logout)

    @pytest.mark.makelivecalls
    def test_minimal(self):
        runner = CliRunner()
        result_status = runner.invoke(status)
        assert 'settings id:' not in result_status.output

        result = runner.invoke(settings, ['createorpatch', self.test_name])
        assert_success(result)
        json_result = json.loads(result.output)
        assert json_result['name'] == self.test_name
        assert json_result['controllerZoneId'] == 'defaultzone'
        assert json_result['lgZoneIds'] == {'defaultzone': 1}
        assert json_result['nextRunId'] == 1

        result_status = runner.invoke(status)
        assert 'settings id: %s' % json_result['id'] in result_status.output

    @pytest.mark.makelivecalls
    def test_all_options(self):
        runner = CliRunner()
        result = runner.invoke(settings,
                               ['createorpatch', self.test_name, '--description', 'test description ',
                                '--scenario', 'scenario name', '--zone', 'defaultzone',
                                '--lgs', 'defaultzone:5,UdFyn:1', '--naming-pattern', 'test_${runID}'])
        assert_success(result)
        json_result = json.loads(result.output)
        assert json_result['name'] == self.test_name
        assert json_result['description'] == 'test description '
        assert json_result['scenarioName'] == 'scenario name'
        assert json_result['controllerZoneId'] == 'defaultzone'
        assert json_result['lgZoneIds']['defaultzone'] == 5
        assert json_result['lgZoneIds']['UdFyn'] == 1
        assert json_result['testResultNamingPattern'] == 'test_${runID}'

        result = runner.invoke(settings, ['delete', self.test_name])
        assert_success(result)

    def test_error_invalid_json(self, valid_data):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('bad.json', 'w') as f:
                f.write('{"key": not valid,,,}')
            result = runner.invoke(settings, ['createorpatch', '--file', 'bad.json', valid_data.test_settings_id])
            assert result.exit_code == 1
            assert 'Error: Expecting value: line 1 column 9 (char 8)' in result.output
            assert 'This command requires a valid Json input' in result.output

    def test_error_not_logged_in(self):
        runner = CliRunner()
        result_logout = runner.invoke(logout)
        assert_success(result_logout)

        result = runner.invoke(settings, ['createorpatch', 'any'])
        assert result.exit_code == 1
        assert 'You aren\'t logged' in str(result.output)
