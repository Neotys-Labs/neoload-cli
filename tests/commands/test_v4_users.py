import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud
from commands.v4_users import cli

USER_ID = 'usr-abc-123'
WORKSPACE_ID = '5e3acde2e860a132744ca916'


def _make_response(status_code, content=b''):
    r = Response()
    r.status_code = status_code
    r._content = content
    return r


@pytest.mark.usefixtures("neoload_login")
class TestV4Users:

    def test_missing_command(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_ls(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [{'id': USER_ID}])
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert 'users' in captured['ep']

    def test_create(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': USER_ID})
        runner = CliRunner()
        body = json.dumps({'login': 'user@example.com', 'role': 'TESTER'})
        result = runner.invoke(cli, ['create', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'users' in captured['ep']
        assert captured['data']['login'] == 'user@example.com'

    def test_get(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'id': USER_ID})
        runner = CliRunner()
        result = runner.invoke(cli, ['get', USER_ID])
        assert result.exit_code == 0
        assert USER_ID in captured['ep']

    def test_get_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['get'])
        assert result.exit_code != 0

    def test_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': USER_ID})
        runner = CliRunner()
        body = json.dumps({'role': 'ADMIN'})
        result = runner.invoke(cli, ['patch', USER_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert USER_ID in captured['ep']

    def test_patch_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['patch'])
        assert result.exit_code != 0

    def test_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'delete', lambda ep: captured.update({'ep': ep}) or _make_response(204))
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', USER_ID])
        assert result.exit_code == 0
        assert 'User deleted.' in result.output
        assert USER_ID in captured['ep']

    def test_delete_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['delete'])
        assert result.exit_code != 0

    def test_workspaces_ls(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [{'id': WORKSPACE_ID}])
        runner = CliRunner()
        result = runner.invoke(cli, ['workspaces-ls', USER_ID])
        assert result.exit_code == 0
        assert USER_ID in captured['ep']
        assert 'workspaces' in captured['ep']

    def test_workspaces_add_with_workspace_id_flag(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'put', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'ok': True})
        runner = CliRunner()
        result = runner.invoke(cli, ['workspaces-add', USER_ID, '--workspace-id', WORKSPACE_ID])
        assert result.exit_code == 0
        assert USER_ID in captured['ep']
        assert captured['data']['workspaceId'] == WORKSPACE_ID

    def test_workspaces_add_with_file(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'put', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'ok': True})
        runner = CliRunner()
        body = json.dumps({'workspaceId': WORKSPACE_ID})
        result = runner.invoke(cli, ['workspaces-add', USER_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert captured['data']['workspaceId'] == WORKSPACE_ID

    def test_workspaces_remove(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'delete', lambda ep: captured.update({'ep': ep}) or _make_response(204))
        runner = CliRunner()
        result = runner.invoke(cli, ['workspaces-remove', USER_ID, '--workspace-id', WORKSPACE_ID])
        assert result.exit_code == 0
        assert 'User removed from workspace.' in result.output
        assert USER_ID in captured['ep']
        assert WORKSPACE_ID in captured['ep']

    def test_workspaces_remove_missing_workspace_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['workspaces-remove', USER_ID])
        assert result.exit_code != 0
