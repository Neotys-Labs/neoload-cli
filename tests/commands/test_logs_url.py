import json
import re
import pytest
from click.testing import CliRunner
from commands.test_results import cli as results
from commands.logs_url import cli as logs_url
from helpers.test_utils import *
from neoload_cli_lib import user_data


@pytest.mark.authentication
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestLogsUrl:
    def test_logs(self, monkeypatch):
        runner = CliRunner()
        frontend_url = user_data.get_user_data().get_frontend_url()
        result = runner.invoke(logs_url, ['70ed01da-f291-4e29-b75c-1f7977edf252'])
        assert_success(result)
        assert frontend_url + '#!result/70ed01da-f291-4e29-b75c-1f7977edf252/overview\n' == result.output

    def test_logs_with_name(self, monkeypatch):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v2/test-results',
                     '[{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"test-name"}]')
        result_ls = runner.invoke(results, ['ls'])
        assert_success(result_ls)

        json_first_test_result_id = json.loads(result_ls.output)[0]['id']
        json_first_test_result_name = json.loads(result_ls.output)[0]['name']
        mock_api_get_with_pagination(monkeypatch, 'v2/test-results',
                     '[{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s"}]' % json_first_test_result_name)
        result_use = runner.invoke(results, ['use', json_first_test_result_name])
        assert_success(result_use)

        frontend_url = user_data.get_user_data().get_frontend_url()
        result = runner.invoke(logs_url, [json_first_test_result_name])
        assert_success(result)
        assert frontend_url + '#!result/%s/overview\n' % json_first_test_result_id == result.output

    def test_logs_required(self):
        runner = CliRunner()
        result = runner.invoke(logs_url)
        assert re.compile(".*Error: Missing argument [\"']NAME[\"'].*", re.DOTALL).match(result.output) is not None
        assert result.exit_code == 2
