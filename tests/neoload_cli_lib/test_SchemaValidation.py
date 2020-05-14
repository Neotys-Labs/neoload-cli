import pytest

import neoload_cli_lib.schema_validation as schema_validation


@pytest.mark.validation
class TestSchemaValidation:

    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    def test_success(self, datafiles):
        yaml_file_path = datafiles.listdir()[0]
        schema_validation.validate_yaml(yaml_file_path, __schema_url__)

    @pytest.mark.datafiles('tests/neoload_projects/broken_yaml.yaml')
    def test_broken_yaml(self, datafiles):
        yaml_file_path = datafiles.listdir()[0]
        with pytest.raises(Exception) as context:
            schema_validation.validate_yaml(yaml_file_path, __schema_url__)
        assert 'This is not a valid yaml file' in str(context.value)

    @pytest.mark.datafiles('tests/neoload_projects/empty.yaml')
    def test_empty(self, datafiles):
        yaml_file_path = datafiles.listdir()[0]
        with pytest.raises(Exception) as context:
            schema_validation.validate_yaml(yaml_file_path, __schema_url__)
        assert schema_validation.YAML_NOT_CONFIRM_MESSAGE in str(context.value)

    @pytest.mark.datafiles('tests/neoload_projects/invalid_to_schema.yaml')
    def test_invalid_to_schema(self, datafiles):
        yaml_file_path = datafiles.listdir()[0]
        with pytest.raises(Exception) as context:
            schema_validation.validate_yaml(yaml_file_path, __schema_url__)
        assert schema_validation.YAML_NOT_CONFIRM_MESSAGE in str(context.value)

    def test_no_file(self, datafiles):
        with pytest.raises(Exception) as context:
            schema_validation.validate_yaml('/invalid/yaml/file_path', __schema_url__)
        assert 'Unable to open file /invalid/yaml/file_path:' in str(context.value)
        assert 'No such file or directory: \'/invalid/yaml/file_path\'' in str(context.value)
        print(context.value)


__schema_url__ = "https://raw.githubusercontent.com/Neotys-Labs/neoload-models/v3/neoload-project/src/main/resources/as-code.latest.schema.json"
