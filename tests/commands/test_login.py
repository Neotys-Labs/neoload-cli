import pytest
from click.testing import CliRunner
from commands.login import cli as login
from commands.status import cli as status
from helpers.test_utils import *
from neoload_cli_lib import user_data
from neoload_cli_lib.user_data import get_user_data


@pytest.mark.authentication
class TestLogin:
    def test_login_basic(self, monkeypatch):
        if monkeypatch is not None:
            monkeypatch.setattr(user_data, '__compute_version_and_path',
                                lambda: get_user_data().set_url('http://front', 'http://files', '1.2.3'))
        runner = CliRunner()
        result = runner.invoke(login, ['123456789fe70bf4a991ae6d8af62e21c4a00203abcdef'])
        assert_success(result)
        result = runner.invoke(status)
        assert_success(result)
        assert 'You are logged on https://neoload-api.saas.neotys.com/ with token **' in result.output
        assert 'frontend url: http' in result.output
        assert 'file storage url: http' in result.output
        assert 'version: ' in result.output

    def test_login_prompt(self):
        runner = CliRunner()
        result = runner.invoke(login, ['--url', 'someURL'], input='token')
        assert result.exit_code == 1
        assert "Invalid URL 'explore/v2/swagger.yaml': No schema supplied" in str(result)

    def test_login_token_required(self):
        runner = CliRunner()
        result = runner.invoke(login, ['--url', 'someURL'])
        assert result.exception.code == 1
        assert 'Aborted!\n' in result.output  # The prompt was aborted

        result = runner.invoke(login)
        assert result.exception.code == 1
        assert 'Aborted!\n' in result.output  # The prompt was aborted
