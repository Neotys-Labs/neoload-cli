import pytest
from click.testing import CliRunner
from commands.login import cli as login
from commands.test_results import cli as test_results
from commands.logs_url import cli as logs_url
from test_utils import assert_success, mock_api


@pytest.mark.authentication
class TestLogsUrl:
    @pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
    def test_logs_saas(self):
        runner = CliRunner()
        result = runner.invoke(logs_url, ['70ed01da-f291-4e29-b75c-1f7977edf252'])
        assert result.output == 'https://neoload.saas.neotys.com/#!result/70ed01da-f291-4e29-b75c-1f7977edf252/overview\n'
        assert_success(result)

    def test_logs_onprem(self):
        runner = CliRunner()
        login_result = runner.invoke(login, ['--url', 'http://some-onprem-install.fr/',
                                             '123456789fe70bf4a991ae6d8af62e21c4a00203abcdef'])
        assert_success(login_result)

        result = runner.invoke(logs_url, ['70ed01da-f291-4e29-b75c-1f7977edf252'])
        assert result.output == 'http://some-onprem-install.fr/#!result/70ed01da-f291-4e29-b75c-1f7977edf252/overview\n'
        assert_success(result)

    @pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
    def test_logs_with_name(self, monkeypatch):
        mock_api(monkeypatch, 'get', 'v2/test-results',
                 '[{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"test-name"}]')
        runner = CliRunner()
        result_use = runner.invoke(test_results, ['use', 'test-name'])
        assert_success(result_use)
        result = runner.invoke(logs_url, ['test-name'])
        assert result.output == 'https://neoload.saas.neotys.com/#!result/70ed01da-f291-4e29-b75c-1f7977edf252/overview\n'
        assert_success(result)

    @pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
    def test_logs_required(self):
        runner = CliRunner()
        result = runner.invoke(logs_url)
        assert 'Error: Missing argument "NAME"' in result.output
        assert result.exit_code == 2
