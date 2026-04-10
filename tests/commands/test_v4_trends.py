import json
import pytest
from click.testing import CliRunner
from neoload_cli_lib import rest_crud
from commands.v4_trends import cli

TEST_ID = 'test-abc-123'


@pytest.mark.usefixtures("neoload_login")
class TestV4Trends:

    def test_missing_command(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['--test-id', TEST_ID])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_get(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'trends': []})
        runner = CliRunner()
        result = runner.invoke(cli, ['get', '--test-id', TEST_ID])
        assert result.exit_code == 0
        assert 'tests' in captured['ep']
        assert TEST_ID in captured['ep']
        assert 'trends' in captured['ep']

    def test_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'updated': True})
        runner = CliRunner()
        body = json.dumps({'maxRuns': 10})
        result = runner.invoke(cli, ['patch', '--test-id', TEST_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert TEST_ID in captured['ep']
        assert captured['data']['maxRuns'] == 10

    def test_config_get(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'config': {}})
        runner = CliRunner()
        result = runner.invoke(cli, ['config-get', '--test-id', TEST_ID])
        assert result.exit_code == 0
        assert 'configuration' in captured['ep']

    def test_config_put(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'put', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'ok': True})
        runner = CliRunner()
        body = json.dumps({'maxRuns': 5})
        result = runner.invoke(cli, ['config-put', '--test-id', TEST_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'configuration' in captured['ep']
        assert 'dryRun' not in captured['ep']

    def test_config_put_dry_run(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'put', lambda ep, data: captured.update({'ep': ep}) or {'ok': True})
        runner = CliRunner()
        body = json.dumps({'maxRuns': 5})
        result = runner.invoke(cli, ['config-put', '--test-id', TEST_ID, '--dry-run', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'dryRun=true' in captured['ep']

    def test_config_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'ok': True})
        runner = CliRunner()
        body = json.dumps({'maxRuns': 3})
        result = runner.invoke(cli, ['config-patch', '--test-id', TEST_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'configuration' in captured['ep']

    def test_elements(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [])
        runner = CliRunner()
        result = runner.invoke(cli, ['elements', '--test-id', TEST_ID])
        assert result.exit_code == 0
        assert 'elements' in captured['ep']
        assert 'trends' in captured['ep']
