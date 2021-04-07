import pytest
from click.testing import CliRunner

from commands.status import cli as status
from commands.test_settings import cli as settings
from tests.helpers.test_utils import *


@pytest.mark.settings
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestDelete:
    def test_minimal(self, monkeypatch):
        # Create the test to delete
        runner = CliRunner()
        test_name = generate_test_settings_name()
        mock_api_post(monkeypatch, 'v2/tests',
                      '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":""}' % test_name)
        result = runner.invoke(settings, ['create', test_name])
        assert_success(result)
        json_result = json.loads(result.output)

        mock_api_delete_raw(monkeypatch, 'v2/tests/%s' % json_result['id'], 200, '{"id":"%s"}' % json_result['id'])
        result_delete = runner.invoke(settings, ['delete'])  # No need to specify the test id.
        assert_success(result_delete)
        assert '"id": "%s"' % json_result['id'] in result_delete.output

        result_status = runner.invoke(status)
        assert 'settings id:' not in result_status.output

    def test_with_name(self, monkeypatch):
        # Create the test to delete
        runner = CliRunner()
        test_name = 'tototootot'  # generate_test_settings_name()
        mock_api_post(monkeypatch, 'v2/tests',
                      '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":""}' % test_name)
        result = runner.invoke(settings, ['create', test_name])
        assert_success(result)
        json_result = json.loads(result.output)

        mock_api_get_with_pagination(monkeypatch, 'v2/tests',
                     '[{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s"}]' % test_name)
        mock_api_delete_raw(monkeypatch, 'v2/tests/%s' % json_result['id'], 200,
                            '{"id":"%s", "name":"%s"}' % (json_result['id'], test_name))
        result_delete = runner.invoke(settings, ['delete', test_name])
        assert_success(result_delete)
        assert '"name": "%s"' % test_name in result_delete.output

        result_status = runner.invoke(status)
        assert 'settings id:' not in result_status.output

    def test_not_found(self, monkeypatch, invalid_data):
        runner = CliRunner()
        mock_api_delete_raw(monkeypatch, 'v2/tests/%s' % invalid_data.uuid, 404,
                            '{"code":"404", "message": "Test not found."}')
        result = runner.invoke(settings, ['delete', invalid_data.uuid])
        assert 'Test not found' in result.output
        if monkeypatch is None:
            assert result.exit_code == 1
