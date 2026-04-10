import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud
from commands.v4_infrastructure_providers import cli

PROVIDER_ID = 'prov-abc-123'


def _make_response(status_code, content=b''):
    r = Response()
    r.status_code = status_code
    r._content = content
    return r


@pytest.mark.usefixtures("neoload_login")
class TestV4InfrastructureProviders:

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
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [{'id': PROVIDER_ID}])
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert 'infrastructure-providers' in captured['ep']

    def test_create(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': PROVIDER_ID})
        runner = CliRunner()
        body = json.dumps({'name': 'MyProvider', 'type': 'DOCKER'})
        result = runner.invoke(cli, ['create', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'infrastructure-providers' in captured['ep']
        assert captured['data']['name'] == 'MyProvider'

    def test_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': PROVIDER_ID})
        runner = CliRunner()
        body = json.dumps({'name': 'UpdatedProvider'})
        result = runner.invoke(cli, ['patch', PROVIDER_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert PROVIDER_ID in captured['ep']

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
        result = runner.invoke(cli, ['delete', PROVIDER_ID])
        assert result.exit_code == 0
        assert 'Infrastructure provider deleted.' in result.output
        assert PROVIDER_ID in captured['ep']

    def test_delete_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['delete'])
        assert result.exit_code != 0
