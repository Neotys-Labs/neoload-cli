import pytest
from click.testing import CliRunner
from commands.test_settings import cli as test


@pytest.mark.test
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestUpdate:
    def test_minimal(self, valid_data):
        runner = CliRunner()
        result = runner.invoke(test, ['update', valid_data.test_id])
        assert 'Test "test name" updated with success' in result.output
        assert result.exit_code == 0

        # update the same test again (the current test id is stored)
        result = runner.invoke(test, ['update'])
        assert 'Test "test name" updated with success' in result.output
        assert result.exit_code == 0

    def test_all_options_input(self, valid_data):
        runner = CliRunner()
        result = runner.invoke(test, ['update', valid_data.test_id],
                               input='{"name":"test name updated", "description":"description updated",'
                                     '"scenario":"scenario updated", "controllerzoneid":"defaultzone",'
                                     '"lgzoneids":{"defaultzone":5,"UdFyn":1}, "testresultnamingpattern":"test_${runId}"}')
        assert 'Test "test name updated" updated with success' in result.output
        assert result.exit_code == 0

        result_ls = runner.invoke(test, ['ls', valid_data.test_id])
        assert valid_data.test_id in result_ls.output
        assert 'test name updated' in result_ls.output
        assert 'description updated' in result_ls.output
        assert 'scenario updated' in result_ls.output
        assert 'defaultzone' in result_ls.output
        assert 'UdFyn' in result_ls.output
        assert result_ls.exit_code == 0

    def test_all_options(self, valid_data):
        runner = CliRunner()
        result = runner.invoke(test,
                               ['update', valid_data.test_id, '--name', 'test updated2', '--description', 'description updated',
                                '--scenario', 'scenario updated', '--controllerzoneid', 'defaultzone',
                                '--lgzoneids', 'defaultzone:5,UdFyn:1', 'testresultnamingpattern', 'test_${runId}'])
        assert 'Test "test name3" created with success with id ' in result.output
        assert result.exit_code == 0
        test_id = str(result.output).split('\n')[1]

        result_ls = runner.invoke(test, ['ls', test_id])
        assert valid_data.test_id in result_ls.output
        assert 'test name updated2' in result_ls.output
        assert 'description updated' in result_ls.output
        assert 'scenario updated' in result_ls.output
        assert 'defaultzone' in result_ls.output
        assert 'UdFyn' in result_ls.output
        assert result_ls.exit_code == 0

    def test_not_found(self, invalid_data):
        runner = CliRunner()
        result = runner.invoke(test, ['update', invalid_data.uuid])
        assert 'Test not found' in result.output
        assert result.exception.code == 1

