from unittest import mock

import json
import pytest

import neoload_cli_lib.schema_validation as schema_validation
from neoload_cli_lib import cli_exception


@pytest.mark.validation
class TestSchemaValidation:

    @pytest.mark.datafiles('tests/neoload_projects/example_1')
    def test_success(self, datafiles):
        yaml_file_path = datafiles / 'default.yaml'
        schema_validation.validate_yaml(yaml_file_path, __schema_url__)

    @pytest.mark.datafiles('tests/neoload_projects/broken_yaml.yaml')
    def test_broken_yaml(self, datafiles):
        yaml_file_path = datafiles / 'broken_yaml.yaml'
        with pytest.raises(Exception) as context:
            schema_validation.validate_yaml(yaml_file_path, __schema_url__)
        assert 'This is not a valid yaml file' in str(context.value)

    @pytest.mark.datafiles('tests/neoload_projects/empty.yaml')
    def test_empty(self, datafiles):
        yaml_file_path = datafiles / 'empty.yaml'
        with pytest.raises(Exception) as context:
            schema_validation.validate_yaml(yaml_file_path, __schema_url__)
        assert 'Empty file' in str(context.value)

    @pytest.mark.datafiles('tests/neoload_projects/invalid_to_schema.yaml')
    def test_invalid_to_schema(self, datafiles):
        yaml_file_path = datafiles / 'invalid_to_schema.yaml'
        with pytest.raises(Exception) as context:
            schema_validation.validate_yaml(yaml_file_path, __schema_url__)
        assert schema_validation.YAML_NOT_CONFIRM_MESSAGE in str(context.value)

    def test_no_file(self):
        with pytest.raises(Exception) as context:
            schema_validation.validate_yaml('/invalid/yaml/file_path', __schema_url__)
        assert 'Unable to open file /invalid/yaml/file_path:' in str(context.value)
        assert 'No such file or directory: \'/invalid/yaml/file_path\'' in str(context.value)
        print(context.value)

    def test_absent_schema_version_resolves_v3_0_schema_url(self):
        spec, key = self._resolve({'name': 'p'})
        assert spec == schema_validation.schema_url_for_version('3.0')
        assert key == '3.0'

    def test_schema_version_3_1_resolves_v3_1_schema_url(self):
        spec, key = self._resolve({'name': 'p', 'schemaVersion': '3.1'})
        assert spec == schema_validation.schema_url_for_version('3.1')
        assert key == '3.1'

    def test_numeric_schema_version_is_normalized(self):
        spec, key = self._resolve({'name': 'p', 'schemaVersion': 3.0})
        assert spec == schema_validation.schema_url_for_version('3.0')
        assert key == '3.0'

    def test_unsupported_schema_version_fails_with_dynamic_list(self):
        with pytest.raises(cli_exception.CliException) as context:
            self._resolve({'name': 'p', 'schemaVersion': '9.9'})
        message = str(context.value)
        assert 'Unsupported schemaVersion "9.9"' in message
        assert '3.0' in message
        assert '3.1' in message

    def test_explicit_schema_spec_skips_compatibility_lookup(self):
        with mock.patch('requests.get') as mock_get:
            spec, key = schema_validation.resolve_schema_spec(
                {'name': 'p', 'schemaVersion': '3.1'}, schema_spec='/tmp/custom-schema.json')
        mock_get.assert_not_called()
        assert spec == '/tmp/custom-schema.json'
        assert key is None

    def test_validate_yaml_downloads_schema_for_declared_version(self, tmp_path):
        yaml_path = tmp_path / 'project.yaml'
        yaml_path.write_text('name: foo\nschemaVersion: "3.1"\n')
        schema = json.dumps({
            "type": "object",
            "required": ["name"],
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string"},
                "schemaVersion": {"type": "string"},
            },
        })
        requested = []

        def fake_get(url, **kwargs):
            requested.append(url)
            response = mock.Mock(status_code=200)
            response.headers.get.return_value = None
            if url.endswith('compatibility.json'):
                response.text = '{"3.0": {}, "3.1": {}}'
            elif url.endswith('schemas/v3.1/as-code.schema.json'):
                response.text = schema
            else:
                raise AssertionError('unexpected schema URL: %s' % url)
            return response

        with mock.patch('requests.get', side_effect=fake_get):
            schema_validation.validate_yaml(str(yaml_path), None)

        assert any(url.endswith('schemas/v3.1/as-code.schema.json') for url in requested)

    def _resolve(self, project):
        response = mock.Mock(status_code=200, text='{"3.0": {}, "3.1": {}}')
        response.headers.get.return_value = None
        with mock.patch('requests.get', return_value=response) as mock_get:
            spec, key = schema_validation.resolve_schema_spec(project, schema_spec=None)
        assert 'compatibility.json' in mock_get.call_args.args[0]
        return spec, key


__schema_url__ = "https://raw.githubusercontent.com/Neotys-Labs/neoload-models/v3/neoload-project/src/main/resources/as-code.latest.schema.json"
