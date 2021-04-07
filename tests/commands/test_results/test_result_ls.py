import pytest
from click.testing import CliRunner
from commands.test_results import cli as results
from commands.logout import cli as logout
from tests.helpers.test_utils import *


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

    def test_list_filter(self, monkeypatch, valid_data):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v2/test-results',
                     '[{"id":"someId", "name":"test-name", "description":".... "},'
                     '{"id":"someId", "name":"test-name-2", "description":".... "}]')
        result_ls = runner.invoke(results, ['ls', '--filter','name=test-name-2'])
        assert_success(result_ls)
        json_result = json.loads(result_ls.output)
        assert len(json_result) == 1

    def test_list_filter_unknown(self, monkeypatch, valid_data):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v2/test-results',
                     '[{"id":"someId", "name":"test-name", "description":".... "},'
                     '{"id":"someId", "name":"test-name-2", "description":".... "}]')
        result_ls = runner.invoke(results, ['ls', '--filter','unknown=test-name-2'])
        assert_success(result_ls)
        json_result = json.loads(result_ls.output)
        assert len(json_result) == 0

    def test_list_filter_regex(self, monkeypatch, valid_data):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v2/test-results',
                     '[{"id":"someId1", "name":"test-name", "description":".... "},'
                     '{"id":"someId2", "name":"test-name-0", "description":"I\'m good !!"},'
                     '{"id":"someId3", "name":"test-name-2", "description":".... "}]')
        result_ls = runner.invoke(results, ['ls', '--filter','name=test-name-[0-9]'])
        assert_success(result_ls)
        json_result = json.loads(result_ls.output)
        assert len(json_result) == 2
        assert json_result[0]['id'] == "someId2"
        assert json_result[1]['id'] == "someId3"

    def test_list_filter_regex_wildcard(self, monkeypatch, valid_data):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v2/test-results',
                     '[{"id":"someId1", "name":"test-name", "description":".... "},'
                     '{"id":"someId2", "name":"test-name-2", "description":".... "}]')
        result_ls = runner.invoke(results, ['ls', '--filter','name=test-name.*'])
        assert_success(result_ls)
        json_result = json.loads(result_ls.output)
        assert len(json_result) == 2
        assert json_result[0]['id'] == "someId1"
        assert json_result[1]['id'] == "someId2"

    def test_list_filter_multiple(self, monkeypatch, valid_data):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v2/test-results',
                     '[{"id":"someId1", "name":"test-name", "description":".... "},'
                     '{"id":"someId2", "name":"test-name-1", "description":"I\'m bad"},'
                     '{"id":"someId3", "name":"test-name-2", "description":"I\'m good !!"}]')
        result_ls = runner.invoke(results, ['ls', '--filter','name=test-name-[0-9];description=^I\'m good*'])
        assert_success(result_ls)
        json_result = json.loads(result_ls.output)
        assert len(json_result) == 1
        assert json_result[0]['id'] == "someId3"

    def test_error_not_logged_in(self):
        runner = CliRunner()
        result_logout = runner.invoke(logout)
        assert_success(result_logout)

        result = runner.invoke(results, ['ls'])
        assert result.exit_code == 1
        assert 'You aren\'t logged' in str(result.output)

    def test_not_found(self, monkeypatch, invalid_data):
        runner = CliRunner()
        mock_api_get(monkeypatch, 'v2/test-results/%s' % invalid_data.uuid, '{"code":"404", "message": "Test result not found."}')
        result = runner.invoke(results, ['ls', invalid_data.uuid])
        assert 'Test result not found' in result.output
        assert result.exit_code == 1
