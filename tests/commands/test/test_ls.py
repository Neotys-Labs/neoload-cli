import pytest
from click.testing import CliRunner
from commands.test_settings import cli as test


@pytest.mark.test
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestLs:
    def test_minimal(self, valid_data):
        runner = CliRunner()
        result = runner.invoke(test, ['ls'])
        assert 'Contains the list of tests' in result.output
        # The list of tests contains at least the valid one
        assert '"id: "%s",' % valid_data.test_id in result.output
        assert result.exception.code == 0

    def test_with_valid_id(self, valid_data):
        runner = CliRunner()
        result = runner.invoke(test, ['ls', valid_data.test_id])
        assert 'Contains Only one test' in result.output
        assert '"id: "%s",' % valid_data.test_id in result.output
        assert result.exception.code == 0

    def test_not_found(self, invalid_data):
        runner = CliRunner()
        result = runner.invoke(test, ['ls', invalid_data.uuid])
        assert 'Test not found' in result.output
        assert result.exception.code == 1

    def test_sort(self):
        raise NotImplementedError('Implement this test')

    def test_pages(self):
        raise NotImplementedError('Implement this test')
