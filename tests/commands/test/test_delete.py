import pytest
from click.testing import CliRunner
from commands.test_settings import cli as test


@pytest.mark.test
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestDelete:
    def test_minimal(self):
        # Create the test to delete
        runner = CliRunner()
        result = runner.invoke(test, ['create', '--name', 'test name to be deleted'])
        assert 'Test "test name" created with success with id' in result.output
        assert result.exit_code == 0
        test_id = str(result.output).split('\n')[1]

        result = runner.invoke(test, ['delete', test_id])
        assert 'Test "test name to be deleted" deleted with success with id\n%s' % test_id in result.output
        assert result.exit_code == 0

    def test_with_memory(self):
        # Create the test to delete
        runner = CliRunner()
        result = runner.invoke(test, ['create', '--name', 'test name to be deleted'])
        assert 'Test "test name" created with success with id' in result.output
        assert result.exit_code == 0
        test_id = str(result.output).split('\n')[1]

        result = runner.invoke(test, ['delete'])  # No need to specify the test id.
        assert 'Test "test name to be deleted" deleted with success with id\n%s' % test_id in result.output
        assert result.exit_code == 0

    def test_not_found(self, invalid_data):
        runner = CliRunner()
        result = runner.invoke(test, ['delete', invalid_data.uuid])
        assert 'Test not found' in result.output
        assert result.exception.code == 1

