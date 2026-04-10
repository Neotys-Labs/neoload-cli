import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud
from commands.v4_sessions import cli


def _make_response(status_code, content=b''):
    r = Response()
    r.status_code = status_code
    r._content = content
    return r


@pytest.mark.usefixtures("neoload_login")
class TestV4Sessions:

    def test_missing_command(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_create(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'token': 'sess-tok'})
        runner = CliRunner()
        body = json.dumps({'login': 'user@example.com', 'password': 'secret'})
        result = runner.invoke(cli, ['create', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'sessions' in captured['ep']
        assert captured['data']['login'] == 'user@example.com'

    def test_create_empty_body(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'token': 'tok'})
        runner = CliRunner()
        result = runner.invoke(cli, ['create'])
        assert result.exit_code == 0
        assert 'sessions' in captured['ep']
        assert captured['data'] == {}

    def test_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'delete', lambda ep: captured.update({'ep': ep}) or _make_response(204))
        runner = CliRunner()
        result = runner.invoke(cli, ['delete'])
        assert result.exit_code == 0
        assert 'Session deleted.' in result.output
        assert 'sessions' in captured['ep']

    def test_delete_with_json_response(self, monkeypatch):
        if monkeypatch is None:
            return
        import json as _json
        body = _json.dumps({'status': 'ok'}).encode()
        monkeypatch.setattr(rest_crud, 'delete', lambda ep: _make_response(200, body))
        runner = CliRunner()
        result = runner.invoke(cli, ['delete'])
        assert result.exit_code == 0
        assert 'ok' in result.output
