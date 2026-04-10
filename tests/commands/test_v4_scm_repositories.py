import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud
from commands.v4_scm_repositories import cli

REPO_ID = 'repo-abc-123'
CHECKOUT_ID = 'co-xyz-789'


def _make_response(status_code, content=b''):
    r = Response()
    r.status_code = status_code
    r._content = content
    return r


@pytest.mark.usefixtures("neoload_login")
class TestV4ScmRepositories:

    def test_missing_command(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_ls(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [{'id': REPO_ID}])
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert 'scm-repositories' in captured['ep']

    def test_create(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': REPO_ID})
        runner = CliRunner()
        body = json.dumps({'name': 'MyRepo', 'url': 'https://github.com/org/repo'})
        result = runner.invoke(cli, ['create', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'scm-repositories' in captured['ep']
        assert captured['data']['name'] == 'MyRepo'

    def test_get(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'id': REPO_ID})
        runner = CliRunner()
        result = runner.invoke(cli, ['get', REPO_ID])
        assert result.exit_code == 0
        assert REPO_ID in captured['ep']

    def test_get_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['get'])
        assert result.exit_code != 0

    def test_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': REPO_ID})
        runner = CliRunner()
        body = json.dumps({'name': 'UpdatedRepo'})
        result = runner.invoke(cli, ['patch', REPO_ID, '--file', '-'], input=body)
        assert result.exit_code == 0
        assert REPO_ID in captured['ep']

    def test_patch_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['patch'])
        assert result.exit_code != 0

    def test_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'delete', lambda ep: captured.update({'ep': ep}) or _make_response(204))
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', REPO_ID])
        assert result.exit_code == 0
        assert 'SCM repository deleted.' in result.output
        assert REPO_ID in captured['ep']

    def test_delete_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['delete'])
        assert result.exit_code != 0

    def test_refs(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or [{'ref': 'main'}])
        runner = CliRunner()
        result = runner.invoke(cli, ['refs', REPO_ID])
        assert result.exit_code == 0
        assert 'references' in captured['ep']
        assert REPO_ID in captured['ep']

    def test_refs_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['refs'])
        assert result.exit_code != 0

    def test_checkout(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: captured.update({'ep': ep, 'data': data}) or {'id': CHECKOUT_ID})
        runner = CliRunner()
        body = json.dumps({'repositoryId': REPO_ID, 'ref': 'main'})
        result = runner.invoke(cli, ['checkout', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert 'checkouts' in captured['ep']

    def test_checkout_status(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, *a, **kw: captured.update({'ep': ep}) or {'status': 'SUCCESS'})
        runner = CliRunner()
        result = runner.invoke(cli, ['checkout-status', '--checkout-id', CHECKOUT_ID])
        assert result.exit_code == 0
        assert CHECKOUT_ID in captured['ep']
        assert 'checkouts' in captured['ep']

    def test_checkout_status_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['checkout-status'])
        assert result.exit_code != 0
