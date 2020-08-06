import pytest
from click.testing import CliRunner
from commands.test_results import cli as results
from commands.logout import cli as logout
from helpers.test_utils import *


@pytest.mark.results
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestResultLs:
    def test_list_all(self, monkeypatch):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v2/test-results',
                     '[{"id":"someId", "name":"test-name", "description":".... "},'
                     '{"id":"someId", "name":"test-name", "description":".... "}]')
        result_ls = runner.invoke(results, ['ls'])
        assert_success(result_ls)
        json_result = json.loads(result_ls.output)
        assert json_result[0]['id'] is not None
        assert json_result[0]['name'] is not None
        assert json_result[0]['description'] is not None

    def test_list_one(self, monkeypatch, valid_data):
        runner = CliRunner()
        mock_api_get(monkeypatch, 'v2/test-results/%s' % valid_data.test_result_id,
                     '{"id":"someId", "name":"test-name", "description":".... "}')
        result_ls = runner.invoke(results, ['ls', valid_data.test_result_id])
        assert_success(result_ls)
        json_result = json.loads(result_ls.output)
        assert json_result['id'] is not None
        assert json_result['name'] is not None
        assert json_result['description'] is not None

    def test_error_not_logged_in(self):
        runner = CliRunner()
        result_logout = runner.invoke(logout)
        assert_success(result_logout)

        result = runner.invoke(results, ['ls'])
        assert result.exit_code == 1
        assert 'You are\'nt logged' in str(result.output)

    def test_not_found(self, monkeypatch, invalid_data):
        runner = CliRunner()
        mock_api_get(monkeypatch, 'v2/test-results/%s' % invalid_data.uuid, '{"code":"404", "message": "Test result not found."}')
        result = runner.invoke(results, ['ls', invalid_data.uuid])
        assert 'Test result not found' in result.output
        assert result.exit_code == 1
