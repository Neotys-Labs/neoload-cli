import pytest
from click.testing import CliRunner
from commands.login import cli as login
from commands.test_settings import cli as test_settings
from commands.logs_url import cli as logs_url


@pytest.mark.authentication
class TestLogin:
    @pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
    def test_logs_saas(self):
        runner = CliRunner()
        result = runner.invoke(logs_url, ['--id', '70ed01da-f291-4e29-b75c-1f7977edf252'])
        assert 'https://neoload.saas.neotys.com/#!result/70ed01da-f291-4e29-b75c-1f7977edf252/overview' == result.output
        assert result.exit_code == 0

    def test_logs_onprem(self):
        runner = CliRunner()
        login_result = runner.invoke(login, ['--url', 'http://some-onprem-install.fr/', '123456789fe70bf4a991ae6d8af62e21c4a00203abcdef'])
        assert 'you are logged on ' in login_result.output
        result = runner.invoke(logs_url, ['--id', '70ed01da-f291-4e29-b75c-1f7977edf252'])
        assert 'http://some-onprem-install.fr/#!result/70ed01da-f291-4e29-b75c-1f7977edf252/overview\n' == result.output
        assert result.exit_code == 0

    @pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
    def test_logs_with_name(self):
        runner = CliRunner()
        result_use = runner.invoke(test_settings, ['use', '--name', 'test-name', '70ed01da-f291-4e29-b75c-1f7977edf252'])
        assert 'success' in result_use.output
        result = runner.invoke(logs_url, ['test-name'])
        assert 'https://neoload.saas.neotys.com/#!result/70ed01da-f291-4e29-b75c-1f7977edf252/overview\n' == result.output
        assert result.exit_code == 0

    @pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
    def test_logs_required(self):
        runner = CliRunner()
        result = runner.invoke(logs_url)
        assert 'Error: Missing argument "NAME"' in result.output
        assert result.exit_code == 2
