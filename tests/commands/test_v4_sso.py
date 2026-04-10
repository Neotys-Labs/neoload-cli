import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud
from commands.v4_sso import cli


def _make_response(status_code, content=b''):
    r = Response()
    r.status_code = status_code
    r._content = content
    return r


@pytest.mark.usefixtures("neoload_login")
class TestV4Sso:

    def test_missing_command(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_config_get(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'provider': 'SAML'})
        runner = CliRunner()
        result = runner.invoke(cli, ['config-get'])
        assert result.exit_code == 0
        assert 'sso' in captured['ep']
        assert 'configuration' in captured['ep']

    def test_config_create(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': 'sso-1'})
        runner = CliRunner()
        body = json.dumps({'provider': 'SAML', 'enabled': True})
        result = runner.invoke(cli, ['config-create', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'configuration' in captured['ep']

    def test_config_put(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'put', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'ok': True})
        runner = CliRunner()
        body = json.dumps({'provider': 'SAML'})
        result = runner.invoke(cli, ['config-put', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'configuration' in captured['ep']

    def test_config_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'ok': True})
        runner = CliRunner()
        body = json.dumps({'enabled': False})
        result = runner.invoke(cli, ['config-patch', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'configuration' in captured['ep']

    def test_config_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'delete', lambda ep: captured.update({'ep': ep}) or _make_response(204))
        runner = CliRunner()
        result = runner.invoke(cli, ['config-delete'])
        assert result.exit_code == 0
        assert 'SSO configuration deleted.' in result.output
        assert 'configuration' in captured['ep']

    def test_config_status(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'status': 'ENABLED'})
        runner = CliRunner()
        result = runner.invoke(cli, ['config-status'])
        assert result.exit_code == 0
        assert 'status' in captured['ep']

    def test_saml_idp_get(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'metadata': 'xml'})
        runner = CliRunner()
        result = runner.invoke(cli, ['saml-idp-get'])
        assert result.exit_code == 0
        assert 'saml2' in captured['ep']
        assert 'identity-provider-metadata' in captured['ep']

    def test_saml_idp_put(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'put', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'ok': True})
        runner = CliRunner()
        body = json.dumps({'metadata': '<xml>'})
        result = runner.invoke(cli, ['saml-idp-put', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'identity-provider-metadata' in captured['ep']

    def test_saml_idp_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'delete', lambda ep: captured.update({'ep': ep}) or _make_response(204))
        runner = CliRunner()
        result = runner.invoke(cli, ['saml-idp-delete'])
        assert result.exit_code == 0
        assert 'SAML identity provider metadata deleted.' in result.output

    def test_saml_sp_metadata(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'metadata': 'sp-xml'})
        runner = CliRunner()
        result = runner.invoke(cli, ['saml-sp-metadata'])
        assert result.exit_code == 0
        assert 'service-provider-metadata' in captured['ep']
