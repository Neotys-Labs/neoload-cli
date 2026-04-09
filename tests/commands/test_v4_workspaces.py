import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud
from neoload_cli_lib.v4 import v4_client
from commands.v4_workspaces import cli


MOCK_WS_ID = '5e3acde2e860a132744ca916'


def _make_response(status_code, content=b''):
    """Create a mock requests.Response."""
    response = Response()
    response.status_code = status_code
    response._content = content
    return response


@pytest.mark.usefixtures("neoload_login")
class TestV4Workspaces:

    def test_ls(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'get',
            lambda endpoint, params=None: {
                'items': [{'id': MOCK_WS_ID, 'name': 'WS1'}],
                'total': 1, 'pageNumber': 0, 'pageSize': 200
            })
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert MOCK_WS_ID in result.output

    def test_ls_multi_page(self, monkeypatch):
        if monkeypatch is None:
            return
        call_count = {'n': 0}
        def mock_get(endpoint, params=None):
            page = call_count['n']
            call_count['n'] += 1
            if page == 0:
                return {'items': [{'id': 'ws-1', 'name': 'A'}], 'total': 2, 'pageNumber': 0, 'pageSize': 200}
            else:
                return {'items': [{'id': 'ws-2', 'name': 'B'}], 'total': 2, 'pageNumber': 1, 'pageSize': 200}
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert 'ws-1' in result.output
        assert 'ws-2' in result.output

    def test_create(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_post(endpoint, data):
            captured['endpoint'] = endpoint
            captured['data'] = data
            return {'id': 'new-ws-id', 'name': data.get('name')}
        monkeypatch.setattr(rest_crud, 'post', mock_post)
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--name', 'MyWS'])
        assert result.exit_code == 0
        assert captured['data'].get('name') == 'MyWS'
        assert 'workspaces' in captured['endpoint']

    def test_create_no_workspace_id_injected(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_post(endpoint, data):
            captured['data'] = data
            return {'id': 'new-ws-id', 'name': data.get('name')}
        monkeypatch.setattr(rest_crud, 'post', mock_post)
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--name', 'NoInject'])
        assert result.exit_code == 0
        assert 'workspaceId' not in captured['data']

    def test_get(self, monkeypatch):
        if monkeypatch is None:
            return
        expected = {'id': MOCK_WS_ID, 'name': 'WS1'}
        captured_endpoint = {}
        def mock_get(endpoint, params=None):
            captured_endpoint['ep'] = endpoint
            return expected
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['get', MOCK_WS_ID])
        assert result.exit_code == 0
        assert MOCK_WS_ID in result.output

    def test_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_patch(endpoint, data):
            captured['endpoint'] = endpoint
            captured['data'] = data
            return {'id': MOCK_WS_ID, 'name': data.get('name')}
        monkeypatch.setattr(rest_crud, 'patch', mock_patch)
        runner = CliRunner()
        result = runner.invoke(cli, ['patch', MOCK_WS_ID, '--name', 'NewName'])
        assert result.exit_code == 0
        assert captured['data'].get('name') == 'NewName'

    def test_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(v4_client, 'v4_delete',
            lambda *args: None)
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', MOCK_WS_ID])
        assert result.exit_code == 0
        assert 'deleted' in result.output.lower()

    def test_delete_with_body(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(v4_client, 'v4_delete',
            lambda *args: {'status': 'gone'})
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', MOCK_WS_ID])
        assert result.exit_code == 0
        assert 'gone' in result.output

    def test_members_ls(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_get(endpoint, params=None):
            captured['endpoint'] = endpoint
            return [{'userId': 'user-1', 'role': 'ADMIN'}]
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['members-ls', MOCK_WS_ID])
        assert result.exit_code == 0
        assert 'workspaces' in captured['endpoint']
        assert MOCK_WS_ID in captured['endpoint']
        assert 'members' in captured['endpoint']

    def test_members_add(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_post(endpoint, data):
            captured['endpoint'] = endpoint
            captured['data'] = data
            return {'userId': 'user-1', 'role': 'TESTER'}
        monkeypatch.setattr(rest_crud, 'post', mock_post)
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('member.json', 'w') as f:
                json.dump({'userId': 'user-1', 'role': 'TESTER'}, f)
            result = runner.invoke(cli, ['members-add', MOCK_WS_ID, '--file', 'member.json'])
        assert result.exit_code == 0
        assert 'workspaces' in captured['endpoint']
        assert 'members' in captured['endpoint']
        assert 'workspaceId' not in captured['data']  # MUST NOT inject workspaceId

    def test_members_add_no_file_raises(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['members-add', MOCK_WS_ID])
        assert result.exit_code != 0
        assert '--file is required' in result.output

    def test_members_remove(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        mock_response = _make_response(204, b'')
        def mock_delete(endpoint):
            captured['endpoint'] = endpoint
            return mock_response
        monkeypatch.setattr(rest_crud, 'delete', mock_delete)
        runner = CliRunner()
        result = runner.invoke(cli, ['members-remove', MOCK_WS_ID, '--login', 'user@example.com'])
        assert result.exit_code == 0
        assert 'login=' in captured['endpoint']
        assert 'user' in captured['endpoint']

    def test_members_remove_url_encodes_special_chars(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        mock_response = _make_response(204, b'')
        def mock_delete(endpoint):
            captured['endpoint'] = endpoint
            return mock_response
        monkeypatch.setattr(rest_crud, 'delete', mock_delete)
        runner = CliRunner()
        result = runner.invoke(cli, ['members-remove', MOCK_WS_ID, '--login', 'user+test@example.com'])
        assert result.exit_code == 0
        # urllib.parse.urlencode should encode + and @ safely
        assert 'login=' in captured['endpoint']
        assert '@' not in captured['endpoint'] or '%40' in captured['endpoint']

    def test_members_remove_no_login_raises(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, ['members-remove', MOCK_WS_ID])
        assert result.exit_code != 0
        assert '--login is required' in result.output

    def test_subscription(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_get(endpoint, params=None):
            captured['endpoint'] = endpoint
            return {'plan': 'enterprise', 'status': 'active'}
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['subscription', MOCK_WS_ID])
        assert result.exit_code == 0
        assert 'workspaces' in captured['endpoint']
        assert MOCK_WS_ID in captured['endpoint']
        assert 'subscription' in captured['endpoint']

    def test_missing_command(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output
