import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud
from commands.v4_events import cli

RESULT_ID = 'res-xyz-789'
EVENT_ID = 'evt-001'
CONTENT_ID = 'cnt-002'


def _make_response(status_code, content=b''):
    r = Response()
    r.status_code = status_code
    r._content = content
    return r


@pytest.mark.usefixtures("neoload_login")
class TestV4Events:

    def test_missing_command(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['--result-id', RESULT_ID])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_ls(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [{'id': EVENT_ID}])
        runner = CliRunner()
        result = runner.invoke(cli, ['ls', '--result-id', RESULT_ID])
        assert result.exit_code == 0
        assert 'results' in captured['ep']
        assert RESULT_ID in captured['ep']
        assert 'events' in captured['ep']

    def test_create(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': EVENT_ID})
        runner = CliRunner()
        body = json.dumps({'type': 'USER', 'name': 'MyEvent'})
        result = runner.invoke(cli, ['create', '--result-id', RESULT_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'events' in captured['ep']
        assert captured['data']['name'] == 'MyEvent'

    def test_get(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'id': EVENT_ID})
        runner = CliRunner()
        result = runner.invoke(cli, ['get', '--result-id', RESULT_ID, '--event-id', EVENT_ID])
        assert result.exit_code == 0
        assert EVENT_ID in captured['ep']

    def test_get_missing_event_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['get', '--result-id', RESULT_ID])
        assert result.exit_code != 0

    def test_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': EVENT_ID})
        runner = CliRunner()
        body = json.dumps({'name': 'Updated'})
        result = runner.invoke(cli, ['patch', '--result-id', RESULT_ID, '--event-id', EVENT_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert EVENT_ID in captured['ep']

    def test_patch_missing_event_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['patch', '--result-id', RESULT_ID])
        assert result.exit_code != 0

    def test_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'delete', lambda ep: captured.update({'ep': ep}) or _make_response(204))
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', '--result-id', RESULT_ID, '--event-id', EVENT_ID])
        assert result.exit_code == 0
        assert 'Event deleted.' in result.output
        assert EVENT_ID in captured['ep']

    def test_delete_missing_event_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', '--result-id', RESULT_ID])
        assert result.exit_code != 0

    def test_errors(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'errors': []})
        runner = CliRunner()
        result = runner.invoke(cli, ['errors', '--result-id', RESULT_ID])
        assert result.exit_code == 0
        assert 'errors' in captured['ep']

    def test_statistics(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'total': 0})
        runner = CliRunner()
        result = runner.invoke(cli, ['statistics', '--result-id', RESULT_ID])
        assert result.exit_code == 0
        assert 'statistics' in captured['ep']

    def test_content(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'content': 'data'})
        runner = CliRunner()
        result = runner.invoke(cli, ['content', '--result-id', RESULT_ID, '--content-id', CONTENT_ID])
        assert result.exit_code == 0
        assert 'contents' in captured['ep']
        assert CONTENT_ID in captured['ep']

    def test_content_missing_content_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['content', '--result-id', RESULT_ID])
        assert result.exit_code != 0
