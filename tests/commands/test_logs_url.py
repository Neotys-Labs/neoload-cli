import json
import re
import pytest
from click.testing import CliRunner
from commands.test_results import cli as results
from commands.logs_url import cli as logs_url
from commands import logs_url as logs_url_mod
from tests.helpers.test_utils import *
from neoload_cli_lib import user_data, tools


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

    def test_logs_cur_uses_meta(self, monkeypatch):
        """Line 25: get_endpoint with name='cur' reads from metadata."""
        test_id = '70ed01da-f291-4e29-b75c-1f7977edf252'
        user_data.set_meta('result id', test_id)

        runner = CliRunner()
        frontend_url = user_data.get_user_data().get_frontend_url()
        result = runner.invoke(logs_url, ['cur'])
        assert_success(result)
        assert '#!result/%s/overview' % test_id in result.output

    def test_logs_fallback_to_meta_required(self, monkeypatch):
        """Line 31: when get_id returns None, get_meta_required is called."""
        test_id = '70ed01da-f291-4e29-b75c-1f7977edf252'
        user_data.set_meta('result id', test_id)

        # Force tools.get_id to return None so the fallback (line 31) triggers
        monkeypatch.setattr(tools, 'get_id', lambda name, resolver, is_id: None)

        runner = CliRunner()
        result = runner.invoke(logs_url, ['some-non-id-name'])
        assert_success(result)
        assert '#!result/%s/overview' % test_id in result.output
