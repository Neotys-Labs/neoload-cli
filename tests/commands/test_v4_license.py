import json
import pytest
from click.testing import CliRunner
from neoload_cli_lib import rest_crud, user_data
from commands.v4_license import cli

MOCK_WORKSPACE_ID = '5e3acde2e860a132744ca916'
LEASE_ID = 'lease-abc-123'


def _mock_workspace(monkeypatch):
    monkeypatch.setattr(user_data, 'get_meta',
                        lambda key: MOCK_WORKSPACE_ID if key == 'workspace id' else None)


@pytest.mark.usefixtures("neoload_login")
class TestV4License:

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
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'type': 'ENTERPRISE'})
        runner = CliRunner()
        result = runner.invoke(cli, ['get'])
        assert result.exit_code == 0
        assert 'license' in captured['ep']

    def test_install(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'status': 'installed'})
        runner = CliRunner()
        body = json.dumps({'licenseKey': 'XXXX-YYYY'})
        result = runner.invoke(cli, ['install', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'license' in captured['ep']
        assert captured['data']['licenseKey'] == 'XXXX-YYYY'

    def test_leases_ls_with_workspace(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, params=None: captured.update({'ep': ep, 'params': params}) or [])
        runner = CliRunner()
        result = runner.invoke(cli, ['leases-ls'])
        assert result.exit_code == 0
        assert 'leases' in captured['ep']
        assert captured['params'] == {'workspaceId': MOCK_WORKSPACE_ID}

    def test_leases_ls_no_workspace(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(user_data, 'get_meta', lambda key: None)
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, params=None: captured.update({'ep': ep, 'params': params}) or [])
        runner = CliRunner()
        result = runner.invoke(cli, ['leases-ls'])
        assert result.exit_code == 0
        assert captured['params'] is None

    def test_leases_create(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': LEASE_ID})
        runner = CliRunner()
        body = json.dumps({'vus': 50})
        result = runner.invoke(cli, ['leases-create', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'leases' in captured['ep']
        assert captured['data']['workspaceId'] == MOCK_WORKSPACE_ID

    def test_leases_get(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'id': LEASE_ID})
        runner = CliRunner()
        result = runner.invoke(cli, ['leases-get', LEASE_ID])
        assert result.exit_code == 0
        assert LEASE_ID in captured['ep']

    def test_leases_get_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['leases-get'])
        assert result.exit_code != 0

    def test_activation_request(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': 'req-1'})
        runner = CliRunner()
        body = json.dumps({'machineId': 'M-123'})
        result = runner.invoke(cli, ['activation-request', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'activation-requests' in captured['ep']

    def test_deactivation_request(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep}) or {'id': 'req-2'})
        runner = CliRunner()
        body = json.dumps({'machineId': 'M-123'})
        result = runner.invoke(cli, ['deactivation-request', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'deactivation-requests' in captured['ep']

    def test_forced_release(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep}) or {'ok': True})
        runner = CliRunner()
        body = json.dumps({'reason': 'expired'})
        result = runner.invoke(cli, ['forced-release', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'forced-releases' in captured['ep']

    def test_release(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep}) or {'ok': True})
        runner = CliRunner()
        body = json.dumps({'reason': 'done'})
        result = runner.invoke(cli, ['release', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'releases' in captured['ep']
