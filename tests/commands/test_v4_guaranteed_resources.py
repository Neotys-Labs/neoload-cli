import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud, user_data
from commands.v4_guaranteed_resources import cli

MOCK_WORKSPACE_ID = '5e3acde2e860a132744ca916'


def _mock_workspace(monkeypatch):
    monkeypatch.setattr(user_data, 'get_meta',
                        lambda key: MOCK_WORKSPACE_ID if key == 'workspace id' else None)


def _make_response(status_code, content=b''):
    r = Response()
    r.status_code = status_code
    r._content = content
    return r


@pytest.mark.usefixtures("neoload_login")
class TestV4GuaranteedResources:

    def test_missing_command(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_ls(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [{'vus': 10}])
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert 'workspaces' in captured['ep']
        assert MOCK_WORKSPACE_ID in captured['ep']
        assert 'guaranteed-resources' in captured['ep']

    def test_create(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'vus': 50})
        runner = CliRunner()
        body = json.dumps({'vus': 50, 'duration': 'PT1H'})
        result = runner.invoke(cli, ['create', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert MOCK_WORKSPACE_ID in captured['ep']
        assert 'guaranteed-resources' in captured['ep']

    def test_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'vus': 100})
        runner = CliRunner()
        body = json.dumps({'vus': 100})
        result = runner.invoke(cli, ['patch', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert MOCK_WORKSPACE_ID in captured['ep']
        assert 'guaranteed-resources' in captured['ep']

    def test_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        monkeypatch.setattr(rest_crud, 'delete', lambda ep: captured.update({'ep': ep}) or _make_response(204))
        runner = CliRunner()
        result = runner.invoke(cli, ['delete'])
        assert result.exit_code == 0
        assert 'Guaranteed resources deleted.' in result.output
        assert MOCK_WORKSPACE_ID in captured['ep']

    def test_no_workspace_raises(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(user_data, 'get_meta', lambda key: None)
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code != 0
