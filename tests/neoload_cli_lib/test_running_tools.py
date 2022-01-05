import pytest
import sys
import ast
from io import StringIO

from urllib.parse import quote
from neoload_cli_lib import running_tools, rest_crud
from tests.helpers.test_utils import mock_api_get, mock_api_patch
from click.testing import CliRunner

import neoload_cli_lib.user_data as user_data
class TestRunningTools:

    def test_display_status_init(self, monkeypatch):
        mock_api_get( monkeypatch, "v2/test-results/any_id", '{"status": "INIT"}')
        capturedOutput = StringIO() # Create StringIO object
        sys.stdout = capturedOutput # Redirect stdout.
        assert running_tools.display_status("any_id", data_lock = {}) # Call function and test returned value
        assert  "Status: INIT\n" == capturedOutput.getvalue() # Test print
        sys.stdout = sys.__stdout__ # Reset redirect.

    def test_display_status_terminated(self, monkeypatch):
        mock_api_get( monkeypatch, "v2/test-results/any_id", '{"status": "INIT"}')
        assert running_tools.display_status("any_id", data_lock = {})
    
    def test_display_status_terminated_with_data(self, monkeypatch):
        mock_api_get( monkeypatch, "v2/test-results/any_id", '{"status": "TERMINATED"}')
        mock_api_patch(monkeypatch, "v2/test-results/any_id", '{"isLocked":"true"}')
        data_lock = {'isLocked':'true'}
        assert running_tools.display_status("any_id", data_lock) is False
        assert data_lock == {}

    def test_display_status_running(self, monkeypatch):
        monkeypatch.setattr(rest_crud, 'get', lambda actual_endpoint: ast.literal_eval(self.__return_json(actual_endpoint)))
        assert  running_tools.display_status("any_id", data_lock = {})

    def test_display_status_running_with_data(self, monkeypatch):
        monkeypatch.setattr(rest_crud, 'get', lambda actual_endpoint: ast.literal_eval(self.__return_json(actual_endpoint)))
        mock_api_patch(monkeypatch, "v2/test-results/any_id", '{"isLocked":"true"}')
        data_lock = {'isLocked':'true'}
        assert  running_tools.display_status("any_id", data_lock)
        assert data_lock == {}

    def test_wait(self):
        # TODO add unit test or coverage for function wait from running tools... care there is time sleep 20 sec ...
        assert True

    def __return_json(self, actual_endpoint):
        if actual_endpoint == "v2/test-results/any_id":
            return '{"startDate": 1639586469, "duration":492829 , "status": "RUNNING"}'
        elif actual_endpoint == "v2/test-results/any_id/statistics" :
            return '{"totalRequestCountSuccess": 62758, "totalRequestCountFailure": 25, "totalRequestDurationAverage": 49.45262, "totalRequestCountPerSecond": 127.393074, "totalTransactionCountSuccess": 125501, "totalTransactionCountFailure": 15, "totalTransactionDurationAverage": 136.1283, "totalTransactionCountPerSecond": 254.6847, "totalIterationCountSuccess": 648, "totalIterationCountFailure": 0, "totalGlobalDownloadedBytes": 1036666537, "totalGlobalDownloadedBytesPerSecond": 2103501.5, "totalGlobalCountFailure": 25}'
        else:
            raise Exception('Endpoint NOT mocked : ' + actual_endpoint)
