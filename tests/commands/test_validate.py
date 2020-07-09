import re
import pytest
from click.testing import CliRunner
from commands.validate import cli as validate
import neoload_cli_lib.schema_validation as schema_validation

@pytest.mark.validation
class TestValidate:

    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    def test_success(self, datafiles):
        file_path = datafiles.listdir()[0]
        runner = CliRunner()
        result = runner.invoke(validate, [str(file_path), '--refresh'])
        assert 'Yaml file is valid' in str(result.output)
        assert result.exit_code == 0

    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    def test_no_refresh(self, datafiles):
        file_path = datafiles.listdir()[0]
        runner = CliRunner()
        result = runner.invoke(validate, [str(file_path)])
        assert 'Yaml file is valid' in str(result.output)
        assert result.exit_code == 0

    @pytest.mark.datafiles('tests/neoload_projects/invalid_to_schema.yaml')
    def test_error(self, datafiles):
        file_path = datafiles.listdir()[0]
        runner = CliRunner()
        result = runner.invoke(validate, [str(file_path), '--refresh'])
        assert schema_validation.YAML_NOT_CONFIRM_MESSAGE in str(result.output)
        assert result.exit_code == 1

    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    def test_bad_schema(self, datafiles):
        file_path = datafiles.listdir()[0]
        runner = CliRunner()
        result = runner.invoke(validate, [str(file_path), '--schema-url', 'https://www.neotys.com/', '--refresh'])
        assert 'Error: This is not a valid json schema file' in str(result.output)
        assert 'Expecting value: line 1 column 1' in str(result.output)
        assert result.exit_code == 1

    def test_no_argument(self):
        runner = CliRunner()
        result = runner.invoke(validate)
        assert re.compile(".*Error: Missing argument [\"']FILE[\"'].*", re.DOTALL).match(result.output) is not None
        assert result.exit_code == 2

    @pytest.mark.slow
    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    def test_bad_schema_url(self, datafiles):
        file_path = datafiles.listdir()[0]
        runner = CliRunner()
        result = runner.invoke(validate, [str(file_path), '--schema-url', 'http://invalid.fr', '--refresh'])
        assert 'Max retries exceeded with url' in str(result.output)
        assert 'Failed to establish a new connection' in str(result.output)
        assert 'Error getting the schema from the url: http://invalid.fr' in str(result.output)
        assert result.exit_code == 1
