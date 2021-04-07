import pytest
from click.testing import CliRunner
from commands.workspaces import cli as workspaces
from commands.logout import cli as logout
from tests.helpers.test_utils import *


@pytest.mark.workspaces
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestWorkspaceLs:
    def test_list_all(self, monkeypatch):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v3/workspaces',
                     '[{"id":"someId", "name":"Default workspace", "description":".... "},'
                     '{"id":"someId", "name":"19377", "description":".... "}]')
        result_ls = runner.invoke(workspaces, ['ls'])
        assert_success(result_ls)
        json_result = json.loads(result_ls.output)
        assert json_result[0]['id'] == 'someId'
        assert json_result[0]['name'] == 'Default workspace'
        assert json_result[0]['description'] == '.... '

    def test_list_one(self, monkeypatch, valid_data):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v3/workspaces',
                     '[{"id":"'+valid_data.default_workspace_id+'", "name":"19377", "description":".... "}]')
        result = runner.invoke(workspaces, ['ls', valid_data.default_workspace_id])
        assert_success(result)
        json_result = json.loads(result.output)
        assert len(json_result)==1

    def test_error_not_logged_in(self):
        runner = CliRunner()
        result_logout = runner.invoke(logout)
        assert_success(result_logout)

        result = runner.invoke(workspaces, ['ls'])
        assert result.exit_code == 1
        assert 'You aren\'t logged' in str(result.output)
