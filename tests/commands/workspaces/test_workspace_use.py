import pytest
from click.testing import CliRunner

from commands.status import cli as status
from commands.workspaces import cli as workspaces
from commands.logout import cli as logout
from helpers.test_utils import *


@pytest.mark.workspaces
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestWorkspaceUse:
    def test_use_id(self, monkeypatch, valid_data):
        runner = CliRunner()
        result_use = runner.invoke(workspaces, ['use', valid_data.default_workspace_id])
        assert_success(result_use)
        assert '' == result_use.output
        result_status = runner.invoke(status)
        assert_success(result_status)
        assert 'workspace id: %s' % valid_data.default_workspace_id in result_status.output
        runner.invoke(logout)

    def test_use_name(self, monkeypatch, valid_data):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v3/workspaces',
                     '[{"id":"%s", "name":"Default workspace", "description":".... "},'
                     '{"id":"someId", "name":"19377", "description":".... "}]' % valid_data.default_workspace_id)
        result_use = runner.invoke(workspaces, ['use', 'Default workspace'])
        assert_success(result_use)
        assert '' == result_use.output
        result_status = runner.invoke(status)
        assert_success(result_status)
        assert 'workspace id: %s' % valid_data.default_workspace_id in result_status.output

    def test_use_bad_name(self, monkeypatch, valid_data):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v3/workspaces',
                     '[{"id":"%s", "name":"Default workspace", "description":".... "},'
                     '{"id":"someId", "name":"19377", "description":".... "}]' % valid_data.default_workspace_id)
        result_use = runner.invoke(workspaces, ['use', 'Default workspac_WITH_TYPO'])
        assert result_use.exit_code == 1
        assert "Error: No id associated to the name 'Default workspac_WITH_TYPO'" in result_use.output
