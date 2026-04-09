import json
import pytest
from click.testing import CliRunner
from neoload_cli_lib import rest_crud, user_data
from neoload_cli_lib.v4 import v4_client
from commands.v4_results import cli

MOCK_WORKSPACE_ID = '5e3acde2e860a132744ca916'


def _mock_workspace(monkeypatch):
    monkeypatch.setattr(user_data, 'get_meta',
                        lambda key: MOCK_WORKSPACE_ID if key == 'workspace id' else None)


@pytest.mark.usefixtures("neoload_login")
class TestV4Results:
    def test_ls(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        mock_items = [{'id': 'r1', 'name': 'Result 1'}, {'id': 'r2', 'name': 'Result 2'}]
        monkeypatch.setattr(v4_client, 'v4_list', lambda *args, **kwargs: mock_items)
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert 'r1' in result.output
        assert 'Result 1' in result.output

    def test_get(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        mock_result = {'id': 'result-uuid', 'name': 'My Result'}
        monkeypatch.setattr(v4_client, 'v4_get', lambda *args: mock_result)
        runner = CliRunner()
        result = runner.invoke(cli, ['get', 'result-uuid'])
        assert result.exit_code == 0
        assert 'result-uuid' in result.output

    def test_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        def mock_update(*args, data):
            captured['data'] = data
            return {'id': args[1], **data}
        monkeypatch.setattr(v4_client, 'v4_update', mock_update)
        runner = CliRunner()
        result = runner.invoke(cli, ['patch', 'result-uuid', '--name', 'New Name'])
        assert result.exit_code == 0
        assert captured['data'].get('name') == 'New Name'

    def test_delete_returns_none(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        monkeypatch.setattr(v4_client, 'v4_delete', lambda *args: None)
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', 'result-uuid'])
        assert result.exit_code == 0
        assert 'deleted' in result.output.lower()

    def test_delete_returns_json(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        monkeypatch.setattr(v4_client, 'v4_delete', lambda *args: {'id': 'result-uuid', 'status': 'deleted'})
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', 'result-uuid'])
        assert result.exit_code == 0

    def test_contexts(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        def mock_get(*args):
            captured['args'] = args
            return {'items': []}
        monkeypatch.setattr(v4_client, 'v4_get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['contexts', 'result-uuid-123'])
        assert result.exit_code == 0
        assert captured['args'] == ('results', 'result-uuid-123', 'contexts')

    def test_elements(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        def mock_get(*args):
            captured['args'] = args
            return {'items': []}
        monkeypatch.setattr(v4_client, 'v4_get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['elements', 'result-uuid-123'])
        assert result.exit_code == 0
        assert captured['args'] == ('results', 'result-uuid-123', 'elements')

    def test_monitors(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        def mock_get(*args):
            captured['args'] = args
            return {'items': []}
        monkeypatch.setattr(v4_client, 'v4_get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['monitors', 'result-uuid-123'])
        assert result.exit_code == 0
        assert captured['args'] == ('results', 'result-uuid-123', 'monitors')

    def test_statistics(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        def mock_get(*args):
            captured['args'] = args
            return {'items': []}
        monkeypatch.setattr(v4_client, 'v4_get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['statistics', 'result-uuid-123'])
        assert result.exit_code == 0
        assert captured['args'] == ('results', 'result-uuid-123', 'statistics')

    def test_timeseries(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        def mock_get(*args):
            captured['args'] = args
            return {'items': []}
        monkeypatch.setattr(v4_client, 'v4_get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['timeseries', 'result-uuid-123'])
        assert result.exit_code == 0
        assert captured['args'] == ('results', 'result-uuid-123', 'timeseries')

    def test_search_criteria(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        monkeypatch.setattr(rest_crud, 'get',
            lambda endpoint, params=None: {'projects': [], 'statuses': []})
        runner = CliRunner()
        result = runner.invoke(cli, ['search-criteria'])
        assert result.exit_code == 0

    def test_missing_command(self, monkeypatch):
        if monkeypatch is None:
            return
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_get_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        runner = CliRunner()
        result = runner.invoke(cli, ['get'])
        assert result.exit_code != 0

    def test_patch_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        runner = CliRunner()
        result = runner.invoke(cli, ['patch'])
        assert result.exit_code != 0

    def test_delete_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        runner = CliRunner()
        result = runner.invoke(cli, ['delete'])
        assert result.exit_code != 0

    def test_patch_with_file(self, monkeypatch, tmp_path):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        def mock_update(*args, data):
            captured['data'] = data
            return {'id': args[1], **data}
        monkeypatch.setattr(v4_client, 'v4_update', mock_update)
        json_file = tmp_path / 'body.json'
        json_file.write_text(json.dumps({'name': 'From File', 'description': 'File desc'}))
        runner = CliRunner()
        result = runner.invoke(cli, ['patch', 'result-uuid', '--file', str(json_file)])
        assert result.exit_code == 0
        assert captured['data'].get('name') == 'From File'
