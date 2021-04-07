import pytest
from click.testing import CliRunner
from commands.login import cli as login
from commands.status import cli as status
from tests.helpers.test_utils import *
from neoload_cli_lib import user_data
from neoload_cli_lib.user_data import get_user_data


@pytest.mark.authentication
class TestLogin:
    def test_login_basic(self, monkeypatch, request):
        mock_api_get_raw(monkeypatch, 'v3/information', 200,
                         '{"front_url":"https://neoload.saas.neotys.com/", "filestorage_url":"https://neoload-files.saas.neotys.com", "version":"SaaS"}')
        token = request.config.getoption('--token')
        runner = CliRunner()
        result = runner.invoke(login, ['123456789fe70bf4a991ae6d8af62e21c4a00203abcdef' if token is None else token])
        assert_success(result)
        result = runner.invoke(status)
        assert_success(result)
        assert 'You are logged on https://neoload-api.saas.neotys.com/ with token **' in result.output
        assert 'frontend url: https://neoload.saas.neotys.com' in result.output
        assert 'file storage url: https://neoload-files.saas.neotys.com' in result.output
        assert 'version: SaaS' in result.output

    def test_login_prompt(self, monkeypatch, request):
        mock_api_get_raw(monkeypatch, 'v3/information', 200,
                         '{"front_url":"https://neoload.saas.neotys.com/", "filestorage_url":"https://neoload-files.saas.neotys.com", "version":"SaaS"}')
        token = request.config.getoption('--token')
        runner = CliRunner()
        result = runner.invoke(login, [], input='totoken' if token is None else token)
        assert_success(result)
        result = runner.invoke(status)
        assert_success(result)
        assert 'You are logged on https://neoload-api.saas.neotys.com/ with token **' in result.output
        assert 'frontend url: https://neoload.saas.neotys.com' in result.output
        assert 'file storage url: https://neoload-files.saas.neotys.com' in result.output
        assert 'version: SaaS' in result.output

    def test_login_unauthorized(self, monkeypatch, request):
        mock_api_get_raw(monkeypatch, 'v3/information', 401, '{"message" : "Unauthorized, "}')
        runner = CliRunner()
        result = runner.invoke(login, ['bad_token'])
        assert result.exit_code == 1
        assert '"message" : "Unauthorized' in str(result.output)

    def test_login_nlw_before_2_5_0(self, monkeypatch):
        if monkeypatch is None:
            # Skip this test when using the production environment (the version is always SaaS)
            return

        mock_api_get_raw(monkeypatch, 'v3/information', 404, '')
        if monkeypatch is not None:
            monkeypatch.setattr(user_data, 'get_front_url_by_private_entrypoint',
                                lambda: 'http://old-front')
            monkeypatch.setattr(user_data, 'get_file_storage_from_swagger',
                                lambda: 'http://old-files')
        runner = CliRunner()
        result = runner.invoke(login, ['123456789fe70bf4a991ae6d8af62e21c4a00203abcdef'])
        assert_success(result)
        result = runner.invoke(status)
        assert_success(result)
        assert 'You are logged on https://neoload-api.saas.neotys.com/ with token **' in result.output
        assert 'frontend url: http://old-front' in result.output
        assert 'file storage url: http://old-files' in result.output
        assert 'version: legacy' in result.output

    def test_login_workspace_before_2_5_0(self, monkeypatch):
        if monkeypatch is None:
            # Skip this test when using the production environment (the version is always SaaS)
            return

        mock_api_get_raw(monkeypatch, 'v3/information', 200,
                         '{"front_url":"https://neoload.saas.neotys.com/", "filestorage_url":"https://neoload-files.saas.neotys.com", "version":"2.4.0"}')
        runner = CliRunner()
        result = runner.invoke(login, ['--workspace', '5e3acde2e860a132744ca916',
                                       '123456789fe70bf4a991ae6d8af62e21c4a00203abcdef'])
        assert 'WARNING: The workspace option works only since Neoload Web 2.5.0. The specified workspace is ignored' in result.output
        assert_success(result)
        result = runner.invoke(status)
        assert_success(result)
        assert 'You are logged on https://neoload-api.saas.neotys.com/ with token **' in result.output
        assert 'frontend url: https://neoload.saas.neotys.com/' in result.output
        assert 'file storage url: https://neoload-files.saas.neotys.com' in result.output
        assert 'version: 2.4.0' in result.output

    def test_login_workspace(self, monkeypatch, request):
        mock_api_get_raw(monkeypatch, 'v3/information', 200,
                         '{"front_url":"https://neoload.saas.neotys.com/", "filestorage_url":"https://neoload-files.saas.neotys.com", "version":"SaaS"}')
        token = request.config.getoption('--token')
        runner = CliRunner()
        result = runner.invoke(login, ['--workspace', '5e3acde2e860a132744ca916',
                                       '123456789fe70bf4a991ae6d8af62e21c4a00203abcdef' if token is None else token])
        assert_success(result)
        result = runner.invoke(status)
        assert_success(result)
        assert 'You are logged on https://neoload-api.saas.neotys.com/ with token **' in result.output
        assert 'frontend url: https://neoload.saas.neotys.com' in result.output
        assert 'file storage url: https://neoload-files.saas.neotys.com' in result.output
        assert 'workspace id: 5e3acde2e860a132744ca916' in result.output
        assert 'version: SaaS' in result.output

    def test_login_frontend_url(self, monkeypatch, request):
        mock_api_get_raw(monkeypatch, 'v3/information', 200, '<html>the frontend page</html>')
        token = request.config.getoption('--token')
        runner = CliRunner()
        result = runner.invoke(login, ['--url', 'https://neoload.saas.neotys.com', '123456789fe70bf4a991ae6d8af62e21c4a00203abcdef' if token is None else token])
        assert result.exit_code == 1
        assert 'Error: Unable to parse the response of the server. Did you set the frontend URL instead of the API url ? Details: Expecting value: line 1 column 1' in str(
            result.output)

    def test_login_bad_url(self, monkeypatch):
        runner = CliRunner()
        result = runner.invoke(login, ['--url', 'someURL'], input='token')
        assert result.exit_code == 1
        assert "Unable to reach Neoload Web API. The URL must start with https:// or http://. Details: Invalid URL" in str(
            result.output)

    def test_login_token_required(self):
        runner = CliRunner()
        result = runner.invoke(login, ['--url', 'someURL'])
        assert result.exception.code == 1
        assert 'Aborted!\n' in result.output  # The prompt was aborted

        result = runner.invoke(login)
        assert result.exception.code == 1
        assert 'Aborted!\n' in result.output  # The prompt was aborted
