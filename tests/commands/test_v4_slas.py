import pytest
from click.testing import CliRunner
from neoload_cli_lib import rest_crud
from commands.v4_slas import cli

RESULT_ID = 'res-sla-456'


@pytest.mark.usefixtures("neoload_login")
class TestV4Slas:

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
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [{'id': 'sla-1'}])
        runner = CliRunner()
        result = runner.invoke(cli, ['ls', '--result-id', RESULT_ID])
        assert result.exit_code == 0
        assert 'results' in captured['ep']
        assert RESULT_ID in captured['ep']
        assert 'slas' in captured['ep']

    def test_ls_output_contains_sla_id(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: [{'id': 'sla-777', 'status': 'PASSED'}])
        runner = CliRunner()
        result = runner.invoke(cli, ['ls', '--result-id', RESULT_ID])
        assert result.exit_code == 0
        assert 'sla-777' in result.output
