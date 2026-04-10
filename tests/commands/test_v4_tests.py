import json
import pytest
from click.testing import CliRunner
from requests import Response
from neoload_cli_lib import rest_crud, user_data
from neoload_cli_lib.v4 import v4_client
from commands.v4_tests import cli

MOCK_WORKSPACE_ID = '5e3acde2e860a132744ca916'


def _mock_workspace(monkeypatch):
    """Set up workspace mock for all workspace-aware tests."""
    monkeypatch.setattr(user_data, 'get_meta',
                        lambda key: MOCK_WORKSPACE_ID if key == 'workspace id' else None)


@pytest.mark.usefixtures("neoload_login")
class TestV4Tests:

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
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_list(*args, **kwargs):
            captured['args'] = args
            return [{'id': 'abc-123', 'name': 'Test1'}]

        monkeypatch.setattr(v4_client, 'v4_list', mock_list)
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert 'abc-123' in result.output
        assert 'Test1' in result.output
        assert captured['args'][0] == 'tests'

    def test_create_with_name(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_create(*args, data=None):
            captured['args'] = args
            captured['data'] = data
            return {'id': 'new-id', 'name': data.get('name', '')}

        monkeypatch.setattr(v4_client, 'v4_create', mock_create)
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--name', 'MyTest'])
        assert result.exit_code == 0
        assert captured['args'][0] == 'tests'
        assert captured['data']['name'] == 'MyTest'

    def test_create_with_file(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_create(*args, data=None):
            captured['args'] = args
            captured['data'] = data
            return {'id': 'file-id', 'name': data.get('name', '')}

        monkeypatch.setattr(v4_client, 'v4_create', mock_create)
        runner = CliRunner()
        body = json.dumps({'name': 'FileTest', 'description': 'from file'})
        result = runner.invoke(cli, ['create', '--file', '-'], input=body)
        assert result.exit_code == 0
        assert captured['args'][0] == 'tests'
        assert captured['data']['name'] == 'FileTest'
        assert captured['data']['description'] == 'from file'

    def test_create_file_name_override(self, monkeypatch):
        """Named flags override file values per D-02."""
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_create(*args, data=None):
            captured['args'] = args
            captured['data'] = data
            return {'id': 'override-id', 'name': data.get('name', '')}

        monkeypatch.setattr(v4_client, 'v4_create', mock_create)
        runner = CliRunner()
        body = json.dumps({'name': 'OriginalName'})
        result = runner.invoke(cli, ['create', '--file', '-', '--name', 'OverriddenName'], input=body)
        assert result.exit_code == 0
        assert captured['args'][0] == 'tests'
        assert captured['data']['name'] == 'OverriddenName'

    def test_get(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_get(*args):
            captured['args'] = args
            return {'id': 'test-uuid', 'name': 'MyTest'}

        monkeypatch.setattr(v4_client, 'v4_get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['get', 'test-uuid'])
        assert result.exit_code == 0
        assert 'test-uuid' in result.output
        assert captured['args'] == ('tests', 'test-uuid')

    def test_get_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        runner = CliRunner()
        result = runner.invoke(cli, ['get'])
        assert result.exit_code != 0

    def test_patch(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_update(*args, data=None):
            captured['args'] = args
            captured['data'] = data
            return {'id': 'test-uuid', 'name': data.get('name', '')}

        monkeypatch.setattr(v4_client, 'v4_update', mock_update)
        runner = CliRunner()
        result = runner.invoke(cli, ['patch', 'test-uuid', '--name', 'NewName'])
        assert result.exit_code == 0
        assert captured['args'] == ('tests', 'test-uuid')
        assert captured['data']['name'] == 'NewName'

    def test_patch_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        runner = CliRunner()
        result = runner.invoke(cli, ['patch'])
        assert result.exit_code != 0

    def test_delete(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_delete(*args):
            captured['args'] = args
            return None

        monkeypatch.setattr(v4_client, 'v4_delete', mock_delete)
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', 'test-uuid'])
        assert result.exit_code == 0
        assert 'Test deleted.' in result.output
        assert captured['args'] == ('tests', 'test-uuid')

    def test_delete_with_json_response(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_delete(*args):
            captured['args'] = args
            return {'status': 'deleted', 'id': 'test-uuid'}

        monkeypatch.setattr(v4_client, 'v4_delete', mock_delete)
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', 'test-uuid'])
        assert result.exit_code == 0
        assert 'deleted' in result.output
        assert captured['args'] == ('tests', 'test-uuid')

    def test_delete_with_results_flag(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}

        mock_response = Response()
        mock_response.status_code = 204
        mock_response._content = b''

        def mock_delete(endpoint):
            captured['endpoint'] = endpoint
            return mock_response

        monkeypatch.setattr(rest_crud, 'delete', mock_delete)
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', 'test-uuid', '--delete-results'])
        assert result.exit_code == 0
        assert '?deleteResults=true' in captured['endpoint']
        assert 'tests' in captured['endpoint']
        assert 'Test deleted.' in result.output

    def test_delete_with_results_flag_json_response(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        body = json.dumps({'status': 'deleted'}).encode()

        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = body

        def mock_delete(endpoint):
            captured['endpoint'] = endpoint
            return mock_response

        monkeypatch.setattr(rest_crud, 'delete', mock_delete)
        runner = CliRunner()
        result = runner.invoke(cli, ['delete', 'test-uuid', '--delete-results'])
        assert result.exit_code == 0
        assert '?deleteResults=true' in captured['endpoint']
        assert 'tests' in captured['endpoint']
        assert 'deleted' in result.output

    def test_scenario_get(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_get(*args):
            captured['args'] = args
            return {'name': 'custom', 'scenarioId': 'sc-abc'}

        monkeypatch.setattr(v4_client, 'v4_get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['scenario-get', 'test-uuid', 'custom'])
        assert result.exit_code == 0
        # verify path segments: tests, test-uuid, scenarios, custom
        assert captured['args'] == ('tests', 'test-uuid', 'scenarios', 'custom')
        assert 'custom' in result.output

    def test_scenario_get_missing_id(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        runner = CliRunner()
        result = runner.invoke(cli, ['scenario-get'])
        assert result.exit_code != 0

    def test_scenario_get_missing_scenario_name(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        runner = CliRunner()
        result = runner.invoke(cli, ['scenario-get', 'test-uuid'])
        assert result.exit_code != 0

    def test_scenario_update(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_replace(*args, data=None):
            captured['args'] = args
            captured['data'] = data
            return {'name': 'custom', 'updated': True}

        monkeypatch.setattr(v4_client, 'v4_replace', mock_replace)
        runner = CliRunner()
        scenario_body = json.dumps({'virtualUsers': 10})
        result = runner.invoke(
            cli,
            ['scenario-update', 'test-uuid', 'custom', '--file', '-'],
            input=scenario_body
        )
        assert result.exit_code == 0
        assert captured['args'] == ('tests', 'test-uuid', 'scenarios', 'custom')
        assert captured['data']['virtualUsers'] == 10

    def test_scenario_update_missing_file(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        runner = CliRunner()
        result = runner.invoke(cli, ['scenario-update', 'test-uuid', 'custom'])
        assert result.exit_code != 0

    def test_create_with_description_and_scenario(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_create(*args, data=None):
            captured['args'] = args
            captured['data'] = data
            return {'id': 'new-id', **data}

        monkeypatch.setattr(v4_client, 'v4_create', mock_create)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['create', '--name', 'T1', '--description', 'A test', '--scenario', 'sc1']
        )
        assert result.exit_code == 0
        assert captured['args'][0] == 'tests'
        assert captured['data']['name'] == 'T1'
        assert captured['data']['description'] == 'A test'
        assert captured['data']['scenarioName'] == 'sc1'

    def test_create_invalid_json_file(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--file', '-'], input='not valid json')
        assert result.exit_code != 0
        assert 'valid JSON' in result.output

    @pytest.mark.parametrize("result_list,expected_count", [
        ([{'id': 'a', 'name': 'test1'}], 1),
        ([{'id': 'a'}, {'id': 'b'}, {'id': 'c'}], 3),
        ([], 0),
    ])
    def test_ls_returns_correct_count(self, monkeypatch, result_list, expected_count):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)

        def mock_list(*args, **kwargs):
            return result_list

        monkeypatch.setattr(v4_client, 'v4_list', mock_list)
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        # Each item's id should appear in the output (or output is empty for 0 items)
        for item in result_list:
            assert item['id'] in result.output

    @pytest.mark.parametrize("test_id,expected_field,expected_value", [
        ('uuid-001', 'name', 'Alpha'),
        ('uuid-002', 'name', 'Beta'),
        ('uuid-003', 'name', 'Gamma'),
    ])
    def test_get_returns_correct_fields(self, monkeypatch, test_id, expected_field, expected_value):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)

        def mock_get(*args):
            return {'id': test_id, 'name': expected_value}

        monkeypatch.setattr(v4_client, 'v4_get', mock_get)
        runner = CliRunner()
        result = runner.invoke(cli, ['get', test_id])
        assert result.exit_code == 0
        assert test_id in result.output
        assert expected_value in result.output

    @pytest.mark.parametrize("name,description,scenario_name", [
        ('TestA', 'desc-a', 'sc-a'),
        ('TestB', 'desc-b', 'sc-b'),
    ])
    def test_create_parametrized_fields(self, monkeypatch, name, description, scenario_name):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_create(*args, data=None):
            captured['data'] = data
            return {'id': 'new-id', **data}

        monkeypatch.setattr(v4_client, 'v4_create', mock_create)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['create', '--name', name, '--description', description, '--scenario', scenario_name]
        )
        assert result.exit_code == 0
        assert captured['data']['name'] == name
        assert captured['data']['description'] == description
        assert captured['data']['scenarioName'] == scenario_name
