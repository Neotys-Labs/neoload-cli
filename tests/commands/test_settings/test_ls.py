import pytest
from click.testing import CliRunner
from commands.test_settings import cli as settings
from commands.logout import cli as logout
from tests.helpers.test_utils import *


@pytest.mark.settings
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestLs:
    def test_list_all(self, monkeypatch):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v2/tests',
                     '[{"id":"someId", "name":"test-name", "description":".... "},'
                     '{"id":"someId", "name":"test-name", "description":".... "}]')
        result_ls = runner.invoke(settings, ['ls'])
        assert_success(result_ls)
        json_result = json.loads(result_ls.output)
        assert json_result[0]['id'] is not None
        assert json_result[0]['name'] is not None
        assert json_result[0]['description'] is not None

    def test_list_one(self, monkeypatch, valid_data):
        runner = CliRunner()
        mock_api_get(monkeypatch, 'v2/tests/%s' % valid_data.test_settings_id,
                     '{"id":"someId", "name":"test-name", "description":".... "}')
        result_ls = runner.invoke(settings, ['ls', valid_data.test_settings_id])
        assert_success(result_ls)
        json_result = json.loads(result_ls.output)
        assert json_result['id'] is not None
        assert json_result['name'] is not None
        assert json_result['description'] is not None

    def test_error_not_logged_in(self):
        runner = CliRunner()
        result_logout = runner.invoke(logout)
        assert_success(result_logout)

        result = runner.invoke(settings, ['ls'])
        assert result.exit_code == 1
        assert 'You aren\'t logged' in str(result.output)

    def test_not_found(self, monkeypatch, invalid_data):
        runner = CliRunner()
        mock_api_get(monkeypatch, 'v2/tests/%s' % invalid_data.uuid, '{"code":"404", "message": "Test not found."}')
        result = runner.invoke(settings, ['ls', invalid_data.uuid])
        assert 'Test not found' in result.output
        if monkeypatch is None:
            assert result.exit_code == 1
