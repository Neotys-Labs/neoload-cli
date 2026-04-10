import pytest
import sys
import ast
from io import StringIO
from unittest.mock import MagicMock

from neoload_cli_lib import running_tools, rest_crud, user_data, tools, hooks
from commands import logs_url, test_results
from tests.helpers.test_utils import mock_api_get, mock_api_patch


class TestRunningTools:

    @pytest.mark.usefixtures("neoload_login")
    def test_display_status_init(self, monkeypatch):
        # user_data.do_logout()
        print(user_data.UserData.get_instance())

        mock_api_get(monkeypatch, "v3/workspaces/5e3acde2e860a132744ca916/test-results/any_id", '{"status": "INIT"}')
        capturedOutput = StringIO()  # Create StringIO object
        sys.stdout = capturedOutput  # Redirect stdout.
        assert running_tools.display_status([], "any_id", data_lock={})  # Call function and test returned value
        assert "Status: INIT\n" == capturedOutput.getvalue()  # Test print
        sys.stdout = sys.__stdout__  # Reset redirect.

    def test_display_status_terminated(self, monkeypatch):
        mock_api_get(monkeypatch, "v3/workspaces/5e3acde2e860a132744ca916/test-results/any_id", '{"status": "INIT"}')
        assert running_tools.display_status([], "any_id", data_lock={})

    def test_display_status_terminated_with_data(self, monkeypatch):
        mock_api_get(monkeypatch, "v3/workspaces/5e3acde2e860a132744ca916/test-results/any_id", '{"status": "TERMINATED"}')
        mock_api_patch(monkeypatch, "v3/workspaces/5e3acde2e860a132744ca916/test-results/any_id", '{"isLocked":"true"}')
        data_lock = {'isLocked': 'true'}
        assert running_tools.display_status([], "any_id", data_lock) is False
        assert data_lock == {}

    def test_display_status_running(self, monkeypatch):
        monkeypatch.setattr(rest_crud, 'get',
                            lambda actual_endpoint: ast.literal_eval(self.__return_json(actual_endpoint)))
        assert running_tools.display_status([], "any_id", data_lock={})

    def test_display_status_running_with_data(self, monkeypatch, patch_datetime_now):
        monkeypatch.setattr(rest_crud, 'get',
                            lambda actual_endpoint: ast.literal_eval(self.__return_json(actual_endpoint)))
        mock_api_patch(monkeypatch, "v3/workspaces/5e3acde2e860a132744ca916/test-results/any_id", '{"isLocked":"true"}')
        data_lock = {'isLocked': 'true'}
        capturedOutput = StringIO()  # Create StringIO object
        sys.stdout = capturedOutput  # Redirect stdout.
        assert running_tools.display_status([], "any_id", data_lock)
        assert data_lock == {}
        assert "19698d01:39:28/00:08:12\t Err[25], LGs[--]\t VUs:--\t BPS[2103501.5]\t RPS:--\t avg(rql): 49.45262\n" in capturedOutput.getvalue()
        assert "10.07.18 05:02:40 AM Lock controller kos\n" in capturedOutput.getvalue()
        assert "10.07.18 05:02:43 AM Load generators preparation\n" in capturedOutput.getvalue()
        sys.stdout = sys.__stdout__  # Reset redirect.

    def test_wait(self):
        # TODO add unit test or coverage for function wait from running tools... care there is time sleep 20 sec ...
        assert True

    def __return_json(self, actual_endpoint):
        if actual_endpoint == "v3/workspaces/5e3acde2e860a132744ca916/test-results/any_id":
            return '{"startDate": 1639586469, "duration":492829 , "status": "RUNNING"}'
        elif actual_endpoint == "v3/workspaces/5e3acde2e860a132744ca916/test-results/any_id/statistics":
            return '{"totalRequestCountSuccess": 62758, "totalRequestCountFailure": 25, "totalRequestDurationAverage": 49.45262, "totalRequestCountPerSecond": 127.393074, "totalTransactionCountSuccess": 125501, "totalTransactionCountFailure": 15, "totalTransactionDurationAverage": 136.1283, "totalTransactionCountPerSecond": 254.6847, "totalIterationCountSuccess": 648, "totalIterationCountFailure": 0, "totalGlobalDownloadedBytes": 1036666537, "totalGlobalDownloadedBytesPerSecond": 2103501.5, "totalGlobalCountFailure": 25}'
        elif actual_endpoint == "v3/workspaces/5e3acde2e860a132744ca916/test-results/any_id/logs":
            return '[{"content": "Lock controller kos","timestamp": 1531224160013,"type": "workflow"}, {"content": "GETTING_AVAILABLE_LGS","timestamp": 1531224163007,"type": "workflow"}]'
        else:
            raise Exception('Endpoint NOT mocked : ' + actual_endpoint)


# ---------------------------------------------------------------------------
# stop — confirm returns False branch (line 117)
# ---------------------------------------------------------------------------

class TestStop:
    def test_stop_returns_false_when_user_declines(self, monkeypatch):
        """When tools.confirm returns False, stop() must return False without posting."""
        monkeypatch.setattr(tools, 'confirm', lambda msg, quit_option=False: False)
        posted = []
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: posted.append(ep))
        result = running_tools.stop("result-id-123", force=False, quit_option=False)
        assert result is False
        assert posted == []

    def test_stop_returns_true_when_user_confirms_graceful(self, monkeypatch):
        monkeypatch.setattr(tools, 'confirm', lambda msg, quit_option=False: True)
        posted = []
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: posted.append((ep, data)))
        monkeypatch.setattr(hooks, 'trig', lambda name, *a, **kw: None)
        result = running_tools.stop("result-id-123", force=False, quit_option=False)
        assert result is True
        assert any("result-id-123" in ep for ep, _ in posted)
        assert any(d.get("stopPolicy") == "GRACEFUL" for _, d in posted)

    def test_stop_returns_true_when_user_confirms_force(self, monkeypatch):
        monkeypatch.setattr(tools, 'confirm', lambda msg, quit_option=False: True)
        posted = []
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: posted.append((ep, data)))
        monkeypatch.setattr(hooks, 'trig', lambda name, *a, **kw: None)
        result = running_tools.stop("result-id-456", force=True, quit_option=False)
        assert result is True
        assert any(d.get("stopPolicy") == "TERMINATE" for _, d in posted)


# ---------------------------------------------------------------------------
# header_status — covers lines 52-57
# ---------------------------------------------------------------------------

class TestHeaderStatus:
    def test_header_status_non_interactive(self, monkeypatch, capsys):
        """header_status prints result ID and URL; no browser open in non-interactive mode."""
        monkeypatch.setattr(logs_url, 'get_url', lambda rid: "https://fake.url/results/" + rid)
        monkeypatch.setattr(tools, 'is_user_interactive', lambda: False)
        opened = []
        import webbrowser
        monkeypatch.setattr(webbrowser, 'open_new_tab', lambda url: opened.append(url))

        running_tools.header_status("my-result-id")

        captured = capsys.readouterr()
        assert "my-result-id" in captured.out
        assert "https://fake.url/results/my-result-id" in captured.out
        assert opened == []

    def test_header_status_interactive_opens_browser(self, monkeypatch, capsys):
        """In interactive mode, header_status opens the result URL in a browser tab."""
        monkeypatch.setattr(logs_url, 'get_url', lambda rid: "https://fake.url/results/" + rid)
        monkeypatch.setattr(tools, 'is_user_interactive', lambda: True)
        import time
        monkeypatch.setattr(time, 'sleep', lambda n: None)  # skip actual sleep
        opened = []
        import webbrowser
        monkeypatch.setattr(webbrowser, 'open_new_tab', lambda url: opened.append(url))

        running_tools.header_status("interactive-result")

        assert opened == ["https://fake.url/results/interactive-result"]


# ---------------------------------------------------------------------------
# handler — covers lines 30-34 (SIGINT handler)
# ---------------------------------------------------------------------------

class TestHandler:
    """Tests for the SIGINT handler function.

    Module-level double-underscore names (e.g. __current_id) are stored in
    the module's __dict__ under their literal names — no class-name mangling
    applies at module scope.  We set/restore them via rt.__dict__ directly.
    """

    def test_handler_no_current_id(self, monkeypatch):
        """handler does nothing when __current_id is None (no test running)."""
        import neoload_cli_lib.running_tools as rt
        saved_id = rt.__dict__['__current_id']
        rt.__dict__['__current_id'] = None
        stop_calls = []
        orig_stop = rt.stop
        rt.stop = lambda rid, force, quit_option: stop_calls.append(rid) or False
        try:
            rt.handler(None, None)
            assert stop_calls == []
        finally:
            rt.stop = orig_stop
            rt.__dict__['__current_id'] = saved_id

    def test_handler_with_current_id_calls_stop(self, monkeypatch):
        """handler calls stop when a test is running (non-None __current_id)."""
        import neoload_cli_lib.running_tools as rt
        saved_id = rt.__dict__['__current_id']
        saved_count = rt.__dict__['__count']
        rt.__dict__['__current_id'] = "running-test-id"
        rt.__dict__['__count'] = 0
        stop_calls = []
        orig_stop = rt.stop

        def fake_stop(rid, force, quit_option):
            stop_calls.append((rid, force))
            return False  # returning False so __count is not incremented

        rt.stop = fake_stop
        try:
            rt.handler(None, None)
            assert any(rid == "running-test-id" for rid, _ in stop_calls)
        finally:
            rt.stop = orig_stop
            rt.__dict__['__current_id'] = saved_id
            rt.__dict__['__count'] = saved_count

    def test_handler_increments_count_on_true(self, monkeypatch):
        """handler increments __count when stop returns True."""
        import neoload_cli_lib.running_tools as rt
        saved_id = rt.__dict__['__current_id']
        saved_count = rt.__dict__['__count']
        rt.__dict__['__current_id'] = "test-id"
        rt.__dict__['__count'] = 0
        orig_stop = rt.stop
        rt.stop = lambda rid, force, quit_option: True
        try:
            rt.handler(None, None)
            assert rt.__dict__['__count'] == 1
        finally:
            rt.stop = orig_stop
            rt.__dict__['__current_id'] = saved_id
            rt.__dict__['__count'] = saved_count


# ---------------------------------------------------------------------------
# wait — covers lines 39-48
# ---------------------------------------------------------------------------

class TestWait:
    def test_wait_terminates_after_one_iteration(self, monkeypatch):
        """wait() exits the loop as soon as display_status returns False, then calls system_exit."""
        import neoload_cli_lib.running_tools as rt
        import time

        monkeypatch.setattr(time, 'sleep', lambda n: None)
        monkeypatch.setattr(hooks, 'trig', lambda name, *a, **kw: None)

        # display_status returns False immediately → loop exits after one call
        monkeypatch.setattr(rt, 'display_status', lambda lines, rid, dl: False)
        monkeypatch.setattr(rt, 'header_status', lambda rid: None)

        exit_calls = []
        monkeypatch.setattr(tools, 'system_exit', lambda proc, apply: exit_calls.append(proc))
        monkeypatch.setattr(test_results, 'summary', lambda rid: {'code': 0, 'message': ''})

        rt.wait("wait-result-id", exit_code_sla=True, data_lock={})

        assert exit_calls == [{'code': 0, 'message': ''}]
        # __current_id is reset to None after wait
        assert rt.__dict__['__current_id'] is None
