import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud
from commands.v4_me import cli

TOKEN_NAME = 'my-token'


def _make_response(status_code, content=b''):
    r = Response()
    r.status_code = status_code
    r._content = content
    return r


@pytest.mark.usefixtures("neoload_login")
class TestV4Me:

    def test_missing_command(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_get(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'login': 'user@example.com'})
        runner = CliRunner()
        result = runner.invoke(cli, ['get'])
        assert result.exit_code == 0
        assert 'me' in captured['ep']

    def test_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'login': 'user@example.com'})
        runner = CliRunner()
        body = json.dumps({'firstName': 'Alice'})
        result = runner.invoke(cli, ['patch', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'me' in captured['ep']
        assert captured['data']['firstName'] == 'Alice'

    def test_password(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'put', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'ok': True})
        runner = CliRunner()
        body = json.dumps({'currentPassword': 'old', 'newPassword': 'new'})
        result = runner.invoke(cli, ['password', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'password' in captured['ep']

    def test_tokens_ls(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [{'name': TOKEN_NAME}])
        runner = CliRunner()
        result = runner.invoke(cli, ['tokens-ls'])
        assert result.exit_code == 0
        assert 'tokens' in captured['ep']

    def test_tokens_create(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'name': TOKEN_NAME, 'value': 'tok-xyz'})
        runner = CliRunner()
        body = json.dumps({'name': TOKEN_NAME})
        result = runner.invoke(cli, ['tokens-create', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'tokens' in captured['ep']

    def test_tokens_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'delete', lambda ep: captured.update({'ep': ep}) or _make_response(204))
        runner = CliRunner()
        result = runner.invoke(cli, ['tokens-delete', TOKEN_NAME])
        assert result.exit_code == 0
        assert 'Token deleted.' in result.output
        assert TOKEN_NAME in captured['ep']

    def test_tokens_delete_missing_token(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['tokens-delete'])
        assert result.exit_code != 0

    def test_features(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'features': []})
        runner = CliRunner()
        result = runner.invoke(cli, ['features'])
        assert result.exit_code == 0
        assert 'features' in captured['ep']
