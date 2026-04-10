import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud
from commands.v4_ldap import cli

ENTITY_ID = 'ent-abc-123'
USER_LOGIN = 'alice@example.com'


def _make_response(status_code, content=b''):
    r = Response()
    r.status_code = status_code
    r._content = content
    return r


@pytest.mark.usefixtures("neoload_login")
class TestV4Ldap:

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
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'host': 'ldap.example.com'})
        runner = CliRunner()
        result = runner.invoke(cli, ['config-get'])
        assert result.exit_code == 0
        assert 'ldap' in captured['ep']
        assert 'configuration' in captured['ep']

    def test_config_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'host': 'ldap2.example.com'})
        runner = CliRunner()
        body = json.dumps({'host': 'ldap2.example.com'})
        result = runner.invoke(cli, ['config-patch', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'configuration' in captured['ep']

    def test_entities_ls(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [{'id': ENTITY_ID}])
        runner = CliRunner()
        result = runner.invoke(cli, ['entities-ls'])
        assert result.exit_code == 0
        assert 'authorized-entities' in captured['ep']

    def test_entities_create(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': ENTITY_ID})
        runner = CliRunner()
        body = json.dumps({'dn': 'cn=admins,dc=example,dc=com'})
        result = runner.invoke(cli, ['entities-create', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'authorized-entities' in captured['ep']

    def test_entities_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': ENTITY_ID})
        runner = CliRunner()
        body = json.dumps({'role': 'ADMIN'})
        result = runner.invoke(cli, ['entities-patch', ENTITY_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert ENTITY_ID in captured['ep']

    def test_entities_patch_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['entities-patch'])
        assert result.exit_code != 0

    def test_entities_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'delete', lambda ep: captured.update({'ep': ep}) or _make_response(204))
        runner = CliRunner()
        result = runner.invoke(cli, ['entities-delete', ENTITY_ID])
        assert result.exit_code == 0
        assert 'Authorized entity deleted.' in result.output
        assert ENTITY_ID in captured['ep']

    def test_entities_delete_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['entities-delete'])
        assert result.exit_code != 0

    def test_search_users(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or [{'dn': 'cn=alice'}])
        runner = CliRunner()
        body = json.dumps({'filter': 'alice'})
        result = runner.invoke(cli, ['search-users', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'users' in captured['ep']
        assert 'search' in captured['ep']

    def test_search_groups(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or [{'dn': 'cn=admins'}])
        runner = CliRunner()
        body = json.dumps({'filter': 'admins'})
        result = runner.invoke(cli, ['search-groups', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'groups' in captured['ep']
        assert 'search' in captured['ep']

    def test_search_user_groups(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or [{'dn': 'cn=admins'}])
        runner = CliRunner()
        body = json.dumps({'filter': ''})
        result = runner.invoke(cli, ['search-user-groups', '--login', USER_LOGIN, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert USER_LOGIN in captured['ep']
        assert 'groups' in captured['ep']
        assert 'search' in captured['ep']

    def test_search_user_groups_missing_login(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['search-user-groups'])
        assert result.exit_code != 0
