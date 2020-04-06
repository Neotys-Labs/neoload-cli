import pytest
from click.testing import CliRunner
from commands.test_settings import cli as test


@pytest.mark.test
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestCreate:
    def test_minimal(self):
        runner = CliRunner()
        result = runner.invoke(test, ['create', '--name', 'test name'])
        assert 'Test "test name" created with success with id' in result.output
        assert result.exit_code == 0
        test_id = str(result.output).split('\n')[1]

        result_ls = runner.invoke(test, ['ls', test_id])
        assert test_id in result_ls.output
        assert 'test name' in result_ls.output
        assert result_ls.exit_code == 0

    def test_all_options_input(self):
        runner = CliRunner()
        result = runner.invoke(test, ['create'],
                               input='{"name":"test name2", "description":"description name",'
                                     '"scenario":"scenario name", "controllerzoneid":"defaultzone",'
                                     '"lgzoneids":{"defaultzone":5,"UdFyn":1}, "testresultnamingpattern":"test_${runId}"}')
        assert 'Test "test name2" created with success with id' in result.output
        assert result.exit_code == 0
        test_id = str(result.output).split('\n')[1]

        result_ls = runner.invoke(test, ['ls', test_id])
        assert test_id in result_ls.output
        assert 'test name2' in result_ls.output
        assert 'description name' in result_ls.output
        assert 'scenario name' in result_ls.output
        assert 'defaultzone' in result_ls.output
        assert 'UdFyn' in result_ls.output
        assert result_ls.exit_code == 0

    def test_all_options(self):
        runner = CliRunner()
        result = runner.invoke(test,
                               ['create', '--name', 'test name3', '--description', 'description name',
                                '--scenario', 'scenario name', '--controllerzoneid', 'defaultzone',
                                '--lgzoneids', 'defaultzone:5,UdFyn:1', 'testresultnamingpattern', 'test_${runId}'])
        assert 'Test "test name3" created with success with id ' in result.output
        assert result.exit_code == 0
        test_id = str(result.output).split('\n')[1]

        result_ls = runner.invoke(test, ['ls', test_id])
        assert test_id in result_ls.output
        assert 'test name3' in result_ls.output
        assert 'description name' in result_ls.output
        assert 'scenario name' in result_ls.output
        assert 'defaultzone' in result_ls.output
        assert 'UdFyn' in result_ls.output
        assert result_ls.exit_code == 0

    def test_error_required(self):
        runner = CliRunner()
        result = runner.invoke(test, ['create'])
        assert result.exception.code == 2
        assert 'Error: Missing option "--name"' in result.output
