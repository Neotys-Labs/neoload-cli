import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud
from commands.v4_analytics import cli

RESULT_ID = 'res-abc-123'
ELEMENT_ID = 'elem-001'
MONITOR_ID = 'mon-002'
INTERVAL_ID = 'intv-003'


def _make_response(status_code, content=b''):
    r = Response()
    r.status_code = status_code
    r._content = content
    return r


@pytest.mark.usefixtures("neoload_login")
class TestV4Analytics:

    def test_missing_command(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['--result-id', RESULT_ID])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_element_values(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [{'name': 'elem1'}])
        runner = CliRunner()
        result = runner.invoke(cli, ['element-values', '--result-id', RESULT_ID])
        assert result.exit_code == 0
        assert 'results' in captured['ep']
        assert RESULT_ID in captured['ep']
        assert 'elements' in captured['ep']
        assert 'values' in captured['ep']

    def test_element_timeseries(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'data': []})
        runner = CliRunner()
        result = runner.invoke(cli, ['element-timeseries', '--result-id', RESULT_ID, '--element-id', ELEMENT_ID])
        assert result.exit_code == 0
        assert RESULT_ID in captured['ep']
        assert ELEMENT_ID in captured['ep']
        assert 'results' in captured['ep']
        assert 'elements' in captured['ep']
        assert 'timeseries' in captured['ep']

    def test_element_timeseries_missing_element_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['element-timeseries', '--result-id', RESULT_ID])
        assert result.exit_code != 0

    def test_element_percentiles(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'data': []})
        runner = CliRunner()
        result = runner.invoke(cli, ['element-percentiles', '--result-id', RESULT_ID, '--element-id', ELEMENT_ID])
        assert result.exit_code == 0
        assert RESULT_ID in captured['ep']
        assert ELEMENT_ID in captured['ep']
        assert 'results' in captured['ep']
        assert 'elements' in captured['ep']
        assert 'percentiles' in captured['ep']

    def test_element_percentiles_missing_element_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['element-percentiles', '--result-id', RESULT_ID])
        assert result.exit_code != 0

    def test_monitor_values(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'data': []})
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor-values', '--result-id', RESULT_ID])
        assert result.exit_code == 0
        assert RESULT_ID in captured['ep']
        assert 'results' in captured['ep']
        assert 'monitors' in captured['ep']
        assert 'values' in captured['ep']

    def test_monitor_timeseries(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'data': []})
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor-timeseries', '--result-id', RESULT_ID, '--monitor-id', MONITOR_ID])
        assert result.exit_code == 0
        assert RESULT_ID in captured['ep']
        assert MONITOR_ID in captured['ep']
        assert 'results' in captured['ep']
        assert 'monitors' in captured['ep']
        assert 'timeseries' in captured['ep']

    def test_monitor_timeseries_missing_monitor_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor-timeseries', '--result-id', RESULT_ID])
        assert result.exit_code != 0

    def test_intervals_ls(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [])
        runner = CliRunner()
        result = runner.invoke(cli, ['intervals-ls', '--result-id', RESULT_ID])
        assert result.exit_code == 0
        assert RESULT_ID in captured['ep']
        assert 'results' in captured['ep']
        assert 'intervals' in captured['ep']

    def test_intervals_create(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': 'new-iv'})
        runner = CliRunner()
        body = json.dumps({'name': 'iv1'})
        result = runner.invoke(cli, ['intervals-create', '--result-id', RESULT_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert RESULT_ID in captured['ep']
        assert 'results' in captured['ep']
        assert 'intervals' in captured['ep']
        assert captured['data']['name'] == 'iv1'

    def test_intervals_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': INTERVAL_ID})
        runner = CliRunner()
        body = json.dumps({'name': 'updated'})
        result = runner.invoke(cli, ['intervals-patch', '--result-id', RESULT_ID, '--interval-id', INTERVAL_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert INTERVAL_ID in captured['ep']

    def test_intervals_patch_missing_interval_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['intervals-patch', '--result-id', RESULT_ID])
        assert result.exit_code != 0

    def test_intervals_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'delete', lambda ep: captured.update({'ep': ep}) or _make_response(204))
        runner = CliRunner()
        result = runner.invoke(cli, ['intervals-delete', '--result-id', RESULT_ID, '--interval-id', INTERVAL_ID])
        assert result.exit_code == 0
        assert 'Interval deleted.' in result.output
        assert INTERVAL_ID in captured['ep']

    def test_intervals_delete_missing_interval_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['intervals-delete', '--result-id', RESULT_ID])
        assert result.exit_code != 0

    def test_interval_generation(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'status': 'ok'})
        runner = CliRunner()
        body = json.dumps({'mode': 'auto'})
        result = runner.invoke(cli, ['interval-generation', '--result-id', RESULT_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert RESULT_ID in captured['ep']
        assert 'results' in captured['ep']
        assert 'interval-generation' in captured['ep']

    def test_report(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'url': 'http://example.com/report'})
        runner = CliRunner()
        body = json.dumps({'type': 'pdf'})
        result = runner.invoke(cli, ['report', '--result-id', RESULT_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert RESULT_ID in captured['ep']
        assert 'results' in captured['ep']
        assert 'report' in captured['ep']
