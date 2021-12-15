import pytest
import sys
from io import StringIO

from urllib.parse import quote

from neoload_cli_lib.running_tools import display_status, display_statistics
from commands.run import cli as run

from tests.helpers.test_utils import mock_api_get, mock_api_post, generate_test_result_name, quote
from click.testing import CliRunner

class TestRunningTools:

    def test_display_status(self, monkeypatch):

        #Test printed output
        capturedOutput = StringIO() # Create StringIO object
        sys.stdout = capturedOutput # Redirect stdout.
        assert display_status(self.__mock_result_state_init(), data_lock = {}) is True # Call function and test returned value
        sys.stdout = sys.__stdout__ # Reset redirect.
        assert  "Status: INIT" == capturedOutput.getvalue() # Test print

        #Testing returned values
        assert display_status(self.__mock_result_state_terminated(), data_lock = {}) is False 

        assert  display_status(self.__mock_result_state_running(), data_lock = {'isLocked':'true'}) is True

        assert  display_status(self.__mock_result_state_terminated(), data_lock = {'isLocked':'true'}) is False

        # if monkeypatch is not None:
        #     # TODO To handle a success test with mocks, we need to be able to mock again GET with the
        #     # TODO endpoint v2/test-results to return data (that could evolve until a "terminate" status...)
        #     return
        # runner = CliRunner()
        # random_result_name = generate_test_result_name()
        # if pytest.test_id is None:
        #     pytest.test_id = '70ed01da-f291-4e29-b75c-1f7977edf252'
        # mock_api_get(monkeypatch, 'v2/tests/%s' % pytest.test_id,
        #              '{"id":"%s", "name":"test-name", "nextRunId":1}' % pytest.test_id)
        # mock_api_post(monkeypatch, 'v2/tests/%s/start?testResultName=%s' % (pytest.test_id, quote(random_result_name)),
        #               '{"resultId": "9f54dacd-e793-4553-9f16-d4cc7adba545"}')
        # result_run = runner.invoke(run, ['--name', random_result_name,
        #                                  '--as-code', 'default.yaml,slas/uat.yaml', '--description',
        #                                  'A custom test description containing hashtags like #latest or #issueNum'
        #                                  ])
        # assert result_run.get('isLocked') is False

    def test_wait(self):
        # TODO add unit test or coverage for function wait from reunning tools... care there is time sleep 20 sec ...
        assert True

    def __mock_result_state_init(self):
        return None

    def __mock_result_state_running(self):
        return None

    def __mock_result_state_terminated(self):
        return None
