import json
import pytest
from click.testing import CliRunner
from neoload_cli_lib import rest_crud, user_data
from neoload_cli_lib.v4 import v4_client
from commands.v4_zones import cli


@pytest.mark.usefixtures("neoload_login")
class TestV4Zones:

    def test_ls(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'get',
            lambda endpoint, params=None: {
                'items': [{'id': 'aBcDe', 'name': 'Zone1', 'type': 'STATIC'}],
                'total': 1, 'pageNumber': 0, 'pageSize': 200
            })
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert 'aBcDe' in result.output

    def test_ls_with_type(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_get(endpoint, params=None):
            captured['params'] = params
            return {'items': [], 'total': 0}
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['ls', '--type', 'STATIC'])
        assert result.exit_code == 0
        assert captured['params'].get('type') == 'STATIC'

    def test_ls_type_dynamic(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_get(endpoint, params=None):
            captured['params'] = params
            return {'items': [{'id': 'xYz12', 'type': 'DYNAMIC'}], 'total': 1}
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['ls', '--type', 'DYNAMIC'])
        assert result.exit_code == 0
        assert captured['params'].get('type') == 'DYNAMIC'
        assert 'xYz12' in result.output

    def test_create(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_post(endpoint, data):
            captured['endpoint'] = endpoint
            captured['data'] = data
            return {'id': 'xYz12', 'name': 'NewZone'}
        monkeypatch.setattr(rest_crud, 'post', mock_post)
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--name', 'NewZone', '--type', 'STATIC'])
        assert result.exit_code == 0
        assert captured['data']['name'] == 'NewZone'
        assert captured['data']['type'] == 'STATIC'

    def test_create_does_not_inject_workspace(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_post(endpoint, data):
            captured['data'] = data
            return {'id': 'xYz12', 'name': 'TestZone'}
        monkeypatch.setattr(rest_crud, 'post', mock_post)
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--name', 'TestZone', '--type', 'CLOUD'])
        assert result.exit_code == 0
        # Zones are NOT workspace-scoped: no workspaceId in body
        assert 'workspaceId' not in captured.get('data', {})

    def test_get(self, monkeypatch):
        if monkeypatch is None:
            return
        def mock_v4_get(*args):
            return {'id': 'aBcDe', 'name': 'Zone1', 'type': 'STATIC'}
        monkeypatch.setattr(v4_client, 'v4_get', mock_v4_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['get', 'aBcDe'])
        assert result.exit_code == 0
        assert 'aBcDe' in result.output

    def test_patch_uses_replace(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_replace(*args, data=None):
            captured['called'] = True
            captured['data'] = data
            return {'id': 'aBcDe', 'name': 'Updated'}
        monkeypatch.setattr(v4_client, 'v4_replace', mock_replace)
        runner = CliRunner()
        result = runner.invoke(cli, ['patch', 'aBcDe', '--name', 'Updated'])
        assert result.exit_code == 0
        assert captured.get('called') is True
        assert captured['data']['name'] == 'Updated'

    def test_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(v4_client, 'v4_delete', lambda *args: None)
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', 'aBcDe'])
        assert result.exit_code == 0
        assert 'Zone deleted.' in result.output

    def test_delete_with_response_body(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(v4_client, 'v4_delete',
            lambda *args: {'id': 'aBcDe', 'status': 'accepted'})
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', 'aBcDe'])
        assert result.exit_code == 0
        assert 'aBcDe' in result.output

    def test_missing_command(self, monkeypatch):
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_get_missing_id(self, monkeypatch):
        runner = CliRunner()
        result = runner.invoke(cli, ['get'])
        assert result.exit_code != 0

    def test_patch_missing_id(self, monkeypatch):
        runner = CliRunner()
        result = runner.invoke(cli, ['patch'])
        assert result.exit_code != 0

    def test_delete_missing_id(self, monkeypatch):
        runner = CliRunner()
        result = runner.invoke(cli, ['delete'])
        assert result.exit_code != 0

    def test_ls_pagination(self, monkeypatch):
        if monkeypatch is None:
            return
        call_count = {'n': 0}
        def mock_get(endpoint, params=None):
            page = call_count['n']
            call_count['n'] += 1
            if page == 0:
                return {
                    'items': [{'id': 'zone1'}, {'id': 'zone2'}],
                    'total': 3, 'pageNumber': 0, 'pageSize': 200
                }
            else:
                return {
                    'items': [{'id': 'zone3'}],
                    'total': 3, 'pageNumber': 1, 'pageSize': 200
                }
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert 'zone1' in result.output
        assert 'zone2' in result.output
        assert 'zone3' in result.output
        assert call_count['n'] == 2
