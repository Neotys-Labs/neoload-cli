import pytest
from click.testing import CliRunner
from commands.status import cli as status
from commands.test_results import cli as results
from helpers.test_utils import *


@pytest.mark.results
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestResultDelete:
    def test_minimal(self, monkeypatch, valid_data):
        runner = CliRunner()
        mock_api_delete_raw(monkeypatch, 'v2/test-results/%s' % valid_data.test_result_id_to_delete, 204, '')
        result_delete = runner.invoke(results, ['delete', valid_data.test_result_id_to_delete])
        assert_success(result_delete)
        assert result_delete.output == '\n'

        result_status = runner.invoke(status)
        assert 'result id:' not in result_status.output

    def test_not_found(self, monkeypatch, invalid_data):
        runner = CliRunner()
        mock_api_delete_raw(monkeypatch, 'v2/test-results/%s' % invalid_data.uuid, 404,
                            '{"code":"201", "message": "Test result not found."}')
        result = runner.invoke(results, ['delete', invalid_data.uuid])
        assert 'Test result not found' in result.output
        if monkeypatch is None:
            assert result.exit_code == 1
