import json
import pytest
from click.testing import CliRunner
from neoload_cli_lib import rest_crud
from commands.v4_settings import cli


@pytest.mark.usefixtures("neoload_login")
class TestV4Settings:

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
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'setting': 'value'})
        runner = CliRunner()
        result = runner.invoke(cli, ['get'])
        assert result.exit_code == 0
        assert 'settings' in captured['ep']

    def test_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'setting': 'updated'})
        runner = CliRunner()
        body = json.dumps({'timezone': 'UTC'})
        result = runner.invoke(cli, ['patch', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'settings' in captured['ep']
        assert captured['data']['timezone'] == 'UTC'

    def test_information(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'version': '4.0'})
        runner = CliRunner()
        result = runner.invoke(cli, ['information'])
        assert result.exit_code == 0
        assert 'information' in captured['ep']

    def test_subscription(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'plan': 'enterprise'})
        runner = CliRunner()
        result = runner.invoke(cli, ['subscription'])
        assert result.exit_code == 0
        assert 'subscription' in captured['ep']
