import pytest
from click.testing import CliRunner
from commands.test import cli as test


@pytest.mark.test
class TestDefault:
    def test_default(self):
        runner = CliRunner()
        result = runner.invoke(test, ['default', 'fakeId'])
        assert result.exit_code == 0
        assert 'The default test id is now fakeId' in result.output

    def test_error_required(self):
        runner = CliRunner()
        result = runner.invoke(test, ['default'])
        assert result.exception.code == 2
        assert 'Error: Missing argument "ID"' in result.output
