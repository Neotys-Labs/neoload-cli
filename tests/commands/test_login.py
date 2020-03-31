from click.testing import CliRunner
from commands.login import cli as login


class TestLogin:
    def test_login_basic(self):
        runner = CliRunner()
        result = runner.invoke(login, ['token'])
        assert result.exit_code == 0
        assert result.output == 'login successfully\n'

    def test_login_all_args(self):
        runner = CliRunner()
        result = runner.invoke(login, ['--uri', 'someURL', 'token'])
        assert result.exit_code == 0
        assert result.output in 'login successfully\n'

    def test_login_prompt(self):
        runner = CliRunner()
        result = runner.invoke(login, ['--uri', 'someURL'], input='token')
        assert result.exit_code == 0
        assert result.output in 'login successfully\n'

    def test_login_token_required(self):
        runner = CliRunner()
        result = runner.invoke(login, ['--uri', 'someURL'])
        assert result.exception.code == 1
        assert result.output == '\nAborted!\n'

        runner = CliRunner()
        result = runner.invoke(login)
        assert result.exception.code == 1
        assert result.output == '\nAborted!\n'
