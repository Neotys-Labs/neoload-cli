import json
import re
import pytest
from click.testing import CliRunner
from commands.login import cli as login
from commands.test_results import cli as results
from commands.logs_url import cli as logs_url
from helpers.test_utils import assert_success, mock_api_get
from neoload_cli_lib import user_data
from neoload_cli_lib.user_data import get_user_data


@pytest.mark.authentication
class TestLogsUrl:
    def test_logs(self, monkeypatch):
        runner = CliRunner()
        if monkeypatch is not None:
            monkeypatch.setattr(user_data, '__compute_version_and_path',
                                lambda: get_user_data().set_url('http://front', 'http://files', '1.2.3'))
        login_result = runner.invoke(login, ['123456789fe70bf4a991ae6d8af62e21c4a00203abcdef'])
        assert_success(login_result)

        result = runner.invoke(logs_url, ['70ed01da-f291-4e29-b75c-1f7977edf252'])
        assert_success(result)
        assert re.compile('http[s]?://.*/#!result/.*/overview', re.DOTALL).match(result.output) is not None

    @pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
    def test_logs_with_name(self, monkeypatch):
        runner = CliRunner()
        mock_api_get(monkeypatch, 'v2/test-results',
                     '[{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"test-name"}]')
        result_ls = runner.invoke(results, ['ls'])
        assert_success(result_ls)

        json_first_test_result_id = json.loads(result_ls.output)[0]['id']
        json_first_test_result_name = json.loads(result_ls.output)[0]['name']
        mock_api_get(monkeypatch, 'v2/test-results',
                     '[{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s"}]' % json_first_test_result_name)
        result_use = runner.invoke(results, ['use', json_first_test_result_name])
        assert_success(result_use)

        mock_api_get(monkeypatch, 'nlweb/rest/rest-api/url-api/v1/action/get-front-end-url',
                     '{"frontEndUrl":{"pathFormatMap":{"HOME":"https://neoload.saas.neotys.com/#!",'
                     '"RESULT_OVERVIEW":"https://neoload.saas.neotys.com/#!result/:benchId/overview"}}}')
        result = runner.invoke(logs_url, [json_first_test_result_name])
        assert '#!result/%s/overview' % json_first_test_result_id in result.output
        assert_success(result)

    @pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
    def test_logs_required(self):
        runner = CliRunner()
        result = runner.invoke(logs_url)
        assert re.compile(".*Error: Missing argument [\"']NAME[\"'].*", re.DOTALL).match(result.output) is not None
        assert result.exit_code == 2
