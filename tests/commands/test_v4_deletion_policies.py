import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud, user_data
from commands.v4_deletion_policies import cli

MOCK_WORKSPACE_ID = '5e3acde2e860a132744ca916'
POLICY_ID = 'pol-abc-123'


def _mock_workspace(monkeypatch):
    monkeypatch.setattr(user_data, 'get_meta',
                        lambda key: MOCK_WORKSPACE_ID if key == 'workspace id' else None)


def _make_response(status_code, content=b''):
    r = Response()
    r.status_code = status_code
    r._content = content
    return r


@pytest.mark.usefixtures("neoload_login")
class TestV4DeletionPolicies:

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
        _mock_workspace(monkeypatch)
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, params=None: captured.update({'ep': ep, 'params': params}) or [{'id': POLICY_ID}])
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert 'deletion-policies' in captured['ep']
        assert captured['params'] == {'workspaceId': MOCK_WORKSPACE_ID}

    def test_create(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': POLICY_ID})
        runner = CliRunner()
        body = json.dumps({'name': 'MyPolicy', 'retentionDays': 30})
        result = runner.invoke(cli, ['create', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'deletion-policies' in captured['ep']
        assert captured['data']['workspaceId'] == MOCK_WORKSPACE_ID

    def test_get(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'id': POLICY_ID})
        runner = CliRunner()
        result = runner.invoke(cli, ['get', POLICY_ID])
        assert result.exit_code == 0
        assert POLICY_ID in captured['ep']

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
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': POLICY_ID})
        runner = CliRunner()
        body = json.dumps({'retentionDays': 60})
        result = runner.invoke(cli, ['patch', POLICY_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert POLICY_ID in captured['ep']

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
        result = runner.invoke(cli, ['delete', POLICY_ID])
        assert result.exit_code == 0
        assert 'Deletion policy deleted.' in result.output
        assert POLICY_ID in captured['ep']

    def test_delete_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['delete'])
        assert result.exit_code != 0

    def test_dry_run(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'deletedCount': 5})
        runner = CliRunner()
        body = json.dumps({'retentionDays': 30})
        result = runner.invoke(cli, ['dry-run', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'execution' in captured['ep']
        assert captured['data']['workspaceId'] == MOCK_WORKSPACE_ID
