import pytest
from click.testing import CliRunner
from commands.login import cli as login
from commands.status import cli as status


@pytest.mark.authentication
class TestLogin:
    def test_login_basic(self):
        runner = CliRunner()
        result = runner.invoke(login, ['123456789fe70bf4a991ae6d8af62e21c4a00203abcdef'])
        assert result.exit_code == 0
        assert 'you are logged on https://neoload-api.saas.neotys.com/ with token **' in result.output
        result = runner.invoke(status)
        assert result.exit_code == 0
        assert 'you are logged on https://neoload-api.saas.neotys.com/ with token **' in result.output

    def test_login_all_args(self):
        runner = CliRunner()
        result = runner.invoke(login, ['--url', 'someURL', 'token'])
        assert result.exit_code == 0
        assert 'you are logged on someURL with token **' in result.output

        result = runner.invoke(status)
        assert result.exit_code == 0
        assert 'you are logged on someURL with token **' in result.output

    def test_login_prompt(self):
        runner = CliRunner()
        result = runner.invoke(login, ['--url', 'someURL'], input='token')
        assert result.exit_code == 0
        assert 'you are logged on someURL with token **' in result.output

        result = runner.invoke(status)
        assert result.exit_code == 0
        assert 'you are logged on someURL with token **' in result.output

    def test_login_token_required(self):
        runner = CliRunner()
        result = runner.invoke(login, ['--url', 'someURL'])
        assert result.exception.code == 1
        assert 'Aborted!\n' in result.output  # The prompt was aborted

        result = runner.invoke(login)
        assert result.exception.code == 1
        assert 'Aborted!\n' in result.output  # The prompt was aborted
