"""
Tests targeting coverage gaps in neoload/commands/test_results.py:
- summary command (lines 80, 185-191)
- junitsla command (lines 82, 139-143)
- no-command path (lines 58-59)
- name == "cur" branch (line 62)
- patch with old NLW version (line 114)
- print_compatibility_warning_for_old_nlw (line 134)
- get_id_by_name_or_id() (lines 147-156)
- get_json_summary() (line 160)
- get_sla_data_by_name_or_id() (lines 166-174)
- get_id() helper (lines 195-198)
- get_resolver() (line 269)
- exit_process() all branches (lines 239-265)
- create_json() interactive path is skipped (stdin not a tty in tests)
"""
import sys
import pytest
from click.testing import CliRunner
from commands.test_results import cli as results
from tests.helpers.test_utils import *
import commands.test_results as test_results_module
from neoload_cli_lib import user_data, displayer, rest_crud


# ─────────────────────────────────────────────────────────────────────────────
# Shared sample data helpers
# ─────────────────────────────────────────────────────────────────────────────

_SAMPLE_RESULT = (
    '{"id":"%(id)s","name":"Sample","terminationReason":"POLICY",'
    '"status":"TERMINATED","qualityStatus":"PASSED"}'
)

_EMPTY_SLA = '[]'

_STATS_JSON = (
    '{"totalRequestCountSuccess":100,"totalRequestCountFailure":0,'
    '"totalRequestDurationAverage":50.0,"totalRequestCountPerSecond":10.0,'
    '"totalTransactionCountSuccess":10,"totalTransactionCountFailure":0,'
    '"totalTransactionDurationAverage":200.0,"totalTransactionCountPerSecond":1.0,'
    '"totalIterationCountSuccess":5,"totalIterationCountFailure":0,'
    '"totalGlobalDownloadedBytes":1024,"totalGlobalDownloadedBytesPerSecond":100.0,'
    '"totalGlobalCountFailure":0}'
)


def _make_mock_get(test_result_id, term_reason="POLICY", sla_global=None, sla_test=None, sla_interval=None):
    """Return a mock for rest_crud.get that handles all test-result endpoints.

    The order of checks matters: more specific paths must come before more general ones
    so that '/slas/statistics' is not accidentally matched by '/statistics'.
    """
    sla_global = sla_global if sla_global is not None else []
    sla_test = sla_test if sla_test is not None else []
    sla_interval = sla_interval if sla_interval is not None else []

    result_json = {
        "id": test_result_id,
        "name": "Sample",
        "terminationReason": term_reason,
        "status": "TERMINATED",
        "qualityStatus": "PASSED",
    }
    stats_json = json.loads(_STATS_JSON)

    def _get(endpoint, params=None):
        # More specific checks first
        if endpoint.endswith('/slas/statistics'):
            return sla_global
        if endpoint.endswith('/slas/per-test'):
            return sla_test
        if endpoint.endswith('/slas/per-interval'):
            return sla_interval
        if endpoint.endswith('/statistics'):
            return stats_json
        # plain result endpoint — just the test-result id
        return result_json

    return _get


# ─────────────────────────────────────────────────────────────────────────────
# Test class
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.results
@pytest.mark.usefixtures("neoload_login")
class TestResultSummaryAndCoverage:

    # ── no-command path ──────────────────────────────────────────────────────

    def test_no_command_prints_help_hint(self):
        """Lines 57-59: When no command is given, print a hint and exit cleanly."""
        runner = CliRunner()
        result = runner.invoke(results, [])
        assert result.exit_code == 0
        assert "command is mandatory" in result.output

    # ── name == "cur" branch ─────────────────────────────────────────────────

    def test_use_cur_resolves_from_meta(self, monkeypatch, valid_data):
        """Line 62: When name is 'cur', resolve from stored meta."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        # First, set meta so 'cur' resolves to a real id
        use_result = runner.invoke(results, ['use', valid_data.test_result_id])
        assert_success(use_result)

        # ls cur should resolve to that id
        mock_api_get(monkeypatch, 'v2/test-results/%s' % valid_data.test_result_id,
                     '{"id":"%s","name":"cur-test"}' % valid_data.test_result_id)
        result = runner.invoke(results, ['ls', 'cur'])
        assert_success(result)
        parsed = json.loads(result.output)
        assert parsed['id'] == valid_data.test_result_id

    # ── summary command ───────────────────────────────────────────────────────

    def test_summary_policy_completed(self, monkeypatch, valid_data):
        """Lines 80, 185-191: summary command with POLICY termination exits 0."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid, term_reason="POLICY"))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 0

    def test_summary_failed_to_start(self, monkeypatch, valid_data):
        """exit_process FAILED_TO_START branch → code 2."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid, term_reason="FAILED_TO_START"))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 2

    def test_summary_cancelled(self, monkeypatch, valid_data):
        """exit_process CANCELLED branch."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid, term_reason="CANCELLED"))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 2

    def test_summary_manual_stop(self, monkeypatch, valid_data):
        """exit_process MANUAL branch."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid, term_reason="MANUAL"))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 2

    def test_summary_lg_availability(self, monkeypatch, valid_data):
        """exit_process LG_AVAILABILITY branch."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid, term_reason="LG_AVAILABILITY"))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 2

    def test_summary_license_failure(self, monkeypatch, valid_data):
        """exit_process LICENSE branch."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid, term_reason="LICENSE"))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 2

    def test_summary_unknown_reason(self, monkeypatch, valid_data):
        """exit_process UNKNOWN branch."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid, term_reason="UNKNOWN"))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 2

    def test_summary_reservation_ended(self, monkeypatch, valid_data):
        """exit_process RESERVATION_ENDED branch."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid, term_reason="RESERVATION_ENDED"))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 2

    def test_summary_sla_failures(self, monkeypatch, valid_data):
        """exit_process branch: sla_failure_count > 0 → code 1."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        failing_sla = [{"status": "FAILED"}]
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(
            tid, term_reason="POLICY",
            sla_global=failing_sla, sla_test=[], sla_interval=[]))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 1

    def test_summary_sla_failures_test(self, monkeypatch, valid_data):
        """exit_process: sla failures from sla_test list."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        failing_sla = [{"status": "FAILED"}]
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(
            tid, term_reason="POLICY",
            sla_global=[], sla_test=failing_sla, sla_interval=[]))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 1

    def test_summary_sla_failures_interval(self, monkeypatch, valid_data):
        """exit_process: sla failures from sla_interval list."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        failing_sla = [{"status": "FAILED"}]
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(
            tid, term_reason="POLICY",
            sla_global=[], sla_test=[], sla_interval=failing_sla))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 1

    def test_summary_variable_termination(self, monkeypatch, valid_data):
        """exit_process VARIABLE branch → code 0."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid, term_reason="VARIABLE"))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 0

    def test_summary_completely_unknown_termination(self, monkeypatch, valid_data):
        """exit_process else branch → code 2 with unknown message."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid, term_reason="SOMETHING_NEW"))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        result = runner.invoke(results, ['summary', tid])
        assert result.exit_code == 2

    def test_summary_uses_stored_id_when_no_name(self, monkeypatch, valid_data):
        """Lines 75-76: When no name is given, uses stored meta result id."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        # Store the id first
        runner.invoke(results, ['use', tid])
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid, term_reason="POLICY"))
        monkeypatch.setattr(displayer, 'print_result_summary', lambda *a, **kw: None)
        # Invoke summary with no name — should pick up stored id
        result = runner.invoke(results, ['summary'])
        assert result.exit_code == 0

    # ── junitsla command ──────────────────────────────────────────────────────

    def test_junitsla_creates_file(self, monkeypatch, valid_data, tmp_path):
        """Lines 82, 139-143: junitsla writes a junit XML file."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        junit_path = str(tmp_path / "junit-output.xml")

        calls = []

        def mock_print_junit(*args, **kwargs):
            calls.append(args)

        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid))
        monkeypatch.setattr(displayer, 'print_result_junit', mock_print_junit)
        # store the id first
        runner.invoke(results, ['use', tid])
        result = runner.invoke(results, ['junitsla', '--junit-file', junit_path])
        assert result.exit_code == 0
        assert len(calls) == 1
        # last argument to print_result_junit is the file path
        assert calls[0][-1] == junit_path

    def test_junitsla_with_explicit_id(self, monkeypatch, valid_data, tmp_path):
        """junitsla with explicit test result id."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        junit_path = str(tmp_path / "junit-output2.xml")
        monkeypatch.setattr(rest_crud, 'get', _make_mock_get(tid))
        monkeypatch.setattr(displayer, 'print_result_junit', lambda *a, **kw: None)
        result = runner.invoke(results, ['junitsla', tid, '--junit-file', junit_path])
        assert result.exit_code == 0

    # ── patch with old NLW version ────────────────────────────────────────────

    def test_patch_raises_on_old_version(self, monkeypatch, valid_data):
        """Line 114: patch on NLW < 2.10.0 raises CliException."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        monkeypatch.setattr(user_data, 'is_version_lower_than', lambda v: True)
        result = runner.invoke(results, ['patch', tid], input='{}')
        assert result.exit_code == 1
        assert 'Patch is not implemented' in result.output

    # ── compatibility warning ─────────────────────────────────────────────────

    def test_put_compatibility_warning_for_old_nlw(self, monkeypatch, valid_data):
        """Line 134: compatibility warning logged for old NLW with externalUrl."""
        if monkeypatch is None:
            return
        import logging
        runner = CliRunner()
        tid = valid_data.test_result_id

        mock_api_put(monkeypatch, 'v2/test-results/%s' % tid,
                     '{"id":"%s","name":"test","description":"","qualityStatus":"PASSED",'
                     '"externalUrl":"http://x","externalUrlLabel":"label"}' % tid)

        # Patch is_version_lower_than to return True (old version)
        monkeypatch.setattr(user_data, 'is_version_lower_than', lambda v: True)

        result = runner.invoke(results, [
            'put', tid,
            '--external-url', 'http://x',
            '--external-url-label', 'label',
        ])
        # Should still succeed (warning is logged, not fatal)
        assert result.exit_code == 0

    # ── get_id_by_name_or_id ─────────────────────────────────────────────────

    def test_get_id_by_name_or_id_with_id(self, monkeypatch, valid_data):
        """Lines 147-156: get_id_by_name_or_id() with a UUID passes through directly."""
        if monkeypatch is None:
            return
        tid = valid_data.test_result_id
        monkeypatch.setattr(rest_crud, 'get', lambda ep: {"id": tid, "name": "x"})
        result_id = test_results_module.get_id_by_name_or_id(tid)
        assert result_id == tid

    def test_get_id_by_name_or_id_with_cur(self, monkeypatch, valid_data):
        """Lines 147-148: get_id_by_name_or_id() with 'cur' resolves meta."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        # Store the id
        runner.invoke(results, ['use', tid])
        # Now get_id_by_name_or_id("cur") should return tid
        monkeypatch.setattr(rest_crud, 'get', lambda ep: {"id": tid, "name": "x"})
        result_id = test_results_module.get_id_by_name_or_id("cur")
        assert result_id == tid

    def test_get_id_by_name_or_id_no_id_uses_meta(self, monkeypatch, valid_data):
        """Lines 153-155: get_id_by_name_or_id() with None falls back to meta."""
        if monkeypatch is None:
            return
        runner = CliRunner()
        tid = valid_data.test_result_id
        # Store the id as current meta
        runner.invoke(results, ['use', tid])
        # Pass None as the name — resolver returns None for non-id non-name
        result_id = test_results_module.get_id_by_name_or_id(None)
        assert result_id == tid

    # ── get_json_summary ──────────────────────────────────────────────────────

    def test_get_json_summary(self, monkeypatch, valid_data):
        """Line 160: get_json_summary() returns dict with 'summary' key."""
        if monkeypatch is None:
            return
        tid = valid_data.test_result_id
        expected_result = {"id": tid, "name": "x"}
        monkeypatch.setattr(rest_crud, 'get', lambda ep: expected_result)
        result = test_results_module.get_json_summary(tid)
        assert 'summary' in result
        assert result['summary'] == expected_result

    # ── get_sla_data_by_name_or_id ────────────────────────────────────────────

    def test_get_sla_data_terminated(self, monkeypatch, valid_data):
        """Lines 166-181: get_sla_data_by_name_or_id() with TERMINATED status fetches SLAs."""
        if monkeypatch is None:
            return
        tid = valid_data.test_result_id
        runner = CliRunner()
        runner.invoke(results, ['use', tid])
        mock_get = _make_mock_get(tid, term_reason="POLICY",
                                  sla_global=[{"status": "PASSED"}],
                                  sla_test=[],
                                  sla_interval=[])
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        data = test_results_module.get_sla_data_by_name_or_id(tid)
        assert data['id'] == tid
        assert 'result' in data
        assert 'stats' in data
        assert 'sla_global' in data
        assert 'sla_test' in data
        assert 'sla_interval' in data

    def test_get_sla_data_non_terminated(self, monkeypatch, valid_data):
        """Lines 170-171: When status != TERMINATED, sla_global and sla_test are []."""
        if monkeypatch is None:
            return
        tid = valid_data.test_result_id
        runner = CliRunner()
        runner.invoke(results, ['use', tid])

        stats_json = json.loads(_STATS_JSON)

        def mock_get_running(endpoint):
            if endpoint.endswith('/statistics'):
                return stats_json
            if endpoint.endswith('/slas/per-interval'):
                return []
            # Main result endpoint — status is RUNNING (not TERMINATED)
            return {"id": tid, "name": "x", "terminationReason": "POLICY", "status": "RUNNING"}

        monkeypatch.setattr(rest_crud, 'get', mock_get_running)
        data = test_results_module.get_sla_data_by_name_or_id(tid)
        assert data['sla_global'] == []
        assert data['sla_test'] == []

    # ── get_id() helper ───────────────────────────────────────────────────────

    def test_get_id_with_uuid_returns_as_is(self, valid_data):
        """Line 195-196: get_id() with a UUID returns it unchanged."""
        tid = valid_data.test_result_id
        result = test_results_module.get_id(tid, True)
        assert result == tid

    def test_get_id_with_none_returns_none(self):
        """Line 195: get_id() with None name and is_id=False returns None."""
        result = test_results_module.get_id(None, False)
        assert result is None

    # ── get_resolver ──────────────────────────────────────────────────────────

    def test_get_resolver_returns_resolver(self):
        """Line 269: get_resolver() returns the module-level resolver."""
        resolver = test_results_module.get_resolver()
        assert resolver is not None

    # ── exit_process() unit tests ─────────────────────────────────────────────

    def test_exit_process_failed_to_start(self):
        result = test_results_module.exit_process(
            {"terminationReason": "FAILED_TO_START"}, [], [], [])
        assert result['code'] == 2
        assert "failed to start" in result['message'].lower()

    def test_exit_process_cancelled(self):
        result = test_results_module.exit_process(
            {"terminationReason": "CANCELLED"}, [], [], [])
        assert result['code'] == 2
        assert "cancelled" in result['message'].lower()

    def test_exit_process_manual(self):
        result = test_results_module.exit_process(
            {"terminationReason": "MANUAL"}, [], [], [])
        assert result['code'] == 2
        assert "manually" in result['message'].lower()

    def test_exit_process_lg_availability(self):
        result = test_results_module.exit_process(
            {"terminationReason": "LG_AVAILABILITY"}, [], [], [])
        assert result['code'] == 2
        assert "load generator" in result['message'].lower()

    def test_exit_process_license(self):
        result = test_results_module.exit_process(
            {"terminationReason": "LICENSE"}, [], [], [])
        assert result['code'] == 2
        assert "license" in result['message'].lower()

    def test_exit_process_unknown(self):
        result = test_results_module.exit_process(
            {"terminationReason": "UNKNOWN"}, [], [], [])
        assert result['code'] == 2
        assert "unknown" in result['message'].lower()

    def test_exit_process_reservation_ended(self):
        result = test_results_module.exit_process(
            {"terminationReason": "RESERVATION_ENDED"}, [], [], [])
        assert result['code'] == 2
        assert "reservation" in result['message'].lower()

    def test_exit_process_sla_failures_global(self):
        result = test_results_module.exit_process(
            {"terminationReason": "POLICY"},
            [{"status": "FAILED"}], [], [])
        assert result['code'] == 1
        assert "1 SLAs" in result['message']

    def test_exit_process_sla_failures_multiple(self):
        result = test_results_module.exit_process(
            {"terminationReason": "POLICY"},
            [{"status": "FAILED"}, {"status": "PASSED"}],
            [{"status": "FAILED"}],
            [{"status": "FAILED"}])
        assert result['code'] == 1
        assert "3 SLAs" in result['message']

    def test_exit_process_policy_no_sla_failures(self):
        result = test_results_module.exit_process(
            {"terminationReason": "POLICY"}, [], [], [])
        assert result['code'] == 0
        assert "completed" in result['message'].lower()

    def test_exit_process_variable(self):
        result = test_results_module.exit_process(
            {"terminationReason": "VARIABLE"}, [], [], [])
        assert result['code'] == 0
        assert "variably" in result['message'].lower()

    def test_exit_process_unknown_reason_else_branch(self):
        result = test_results_module.exit_process(
            {"terminationReason": "MYSTERY_REASON"}, [], [], [])
        assert result['code'] == 2
        assert "MYSTERY_REASON" in result['message']
