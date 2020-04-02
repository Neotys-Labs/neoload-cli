import pytest
from click.testing import CliRunner
from commands.validate import cli as validate


@pytest.mark.validation
class TestValidate:

    @pytest.mark.datafiles('../neoload_projects/example_1/everything.yaml')
    def test_success(self, datafiles):
        file_path = datafiles.listdir()[0]
        with open(file_path) as f:
            file_bytes = f.read()
        runner = CliRunner()
        result = runner.invoke(validate, [file_bytes])
        assert 'Yaml file is valid' in str(result.output)
        assert result.exit_code == 0

    @pytest.mark.datafiles('../neoload_projects/invalid_to_schema.yaml')
    def test_error(self, datafiles):
        file_path = datafiles.listdir()[0]
        with open(file_path) as f:
            file_bytes = f.read()
        runner = CliRunner()
        result = runner.invoke(validate, [file_bytes])
        assert 'Wrong Yaml structure' in str(result.output)
        assert 'Additional properties are not allowed (\'ifyourelookingforcutthroat\' was unexpected)' in str(
            result.output)
        assert 'On instance:\n{\'name\': \'NeoLoad-CLI-example-2_0' in str(result.output)
        assert result.exit_code == 1

    def test_bad_schema(self):
        runner = CliRunner()
        result = runner.invoke(validate, ['file_bytes', '--schema-url', 'https://www.neotys.com/'])
        assert 'Error: This is not a valid json schema file' in str(result.output)
        assert 'Expecting value: line 1 column 1' in str(result.output)
        assert result.exit_code == 1

    def test_no_argument(self):
        runner = CliRunner()
        result = runner.invoke(validate)
        assert 'Error: Missing argument "FILE"' in str(result.output)
        assert result.exit_code == 2

    @pytest.mark.slow
    def test_bad_schema_url(self):
        runner = CliRunner()
        result = runner.invoke(validate, ['file_bytes', '--schema-url', 'http://invalid.fr'])
        assert 'Max retries exceeded with url' in str(result.output)
        assert 'Failed to establish a new connection' in str(result.output)
        assert 'Error getting the schema from the url: http://invalid.fr' in str(result.output)
        assert result.exit_code == 1
