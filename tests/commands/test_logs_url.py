import json

import pytest
from click.testing import CliRunner
from commands.login import cli as login
from commands.test_results import cli as test_results
from commands.logs_url import cli as logs_url
from neoload_cli_lib import rest_crud


def assert_success(result_use):
    if result_use.exception is not None:
        assert str(result_use.exception) == ''
    assert result_use.exit_code == 0


def mock_api(monkeypatch, method, endpoint, json_result):
    monkeypatch.setattr(rest_crud, method,
                        lambda actual_endpoint: __return_json(actual_endpoint, endpoint, json_result))
    print('Mock %s %s to return %s' % (method.upper(), endpoint, json_result))


def __return_json(actual_endpoint, expected_endpoint, json_result):
    if actual_endpoint == expected_endpoint:
        return json.loads(json_result)
    raise Exception('Fail ! BAD endpoint.\nActual  : %s\nExpected: %s' % (actual_endpoint, expected_endpoint))


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
