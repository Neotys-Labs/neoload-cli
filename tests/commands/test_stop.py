"""
Tests for neoload/commands/stop.py

Missing lines (from coverage report): 16, 19
  Line 16: raise cli_exception.CliException('No test id is provided')
           — when name is None/empty after checking meta
  Line 19: name = test_results.__resolver.resolve_name(name)
           — when name is not a UUID-style id (non-id string)
"""
import sys
import pytest
from click.testing import CliRunner

sys.path.append('neoload')

from commands.stop import cli as stop_cli
from neoload_cli_lib import user_data, running_tools, tools
from tests.helpers.test_utils import mock_login_get_urls


@pytest.mark.usefixtures("neoload_login")
class TestStop:
    def test_stop_no_name_no_meta_raises(self, monkeypatch):
        """Line 16: no name arg and no meta stored → CliException raised."""
        # Ensure no result id in metadata
        user_data.set_meta('result id', None)

        # Also mock running_tools.stop so we don't actually call the API
        monkeypatch.setattr(running_tools, 'stop', lambda name, force: None)

        runner = CliRunner()
        result = runner.invoke(stop_cli, [])
        # CliException becomes a non-zero exit code
        assert result.exit_code != 0
        assert 'No test id is provided' in result.output

    def test_stop_with_uuid_id(self, monkeypatch):
        """When a UUID id is passed, tools.is_id returns True → resolver skipped."""
        stop_called = {}

        def fake_stop(name, force):
            stop_called['name'] = name
            stop_called['force'] = force

        monkeypatch.setattr(running_tools, 'stop', fake_stop)

        runner = CliRunner()
        result = runner.invoke(stop_cli, ['70ed01da-f291-4e29-b75c-1f7977edf252'])
        assert result.exit_code == 0
        assert stop_called.get('name') == '70ed01da-f291-4e29-b75c-1f7977edf252'
        assert stop_called.get('force') is False

    def test_stop_with_uuid_and_force_flag(self, monkeypatch):
        """Passing --force sets force=True to running_tools.stop."""
        stop_called = {}

        def fake_stop(name, force):
            stop_called['name'] = name
            stop_called['force'] = force

        monkeypatch.setattr(running_tools, 'stop', fake_stop)

        runner = CliRunner()
        result = runner.invoke(stop_cli, ['--force', '70ed01da-f291-4e29-b75c-1f7977edf252'])
        assert result.exit_code == 0
        assert stop_called.get('force') is True

    def test_stop_cur_uses_meta(self, monkeypatch):
        """Using 'cur' as name resolves from metadata."""
        test_id = '70ed01da-f291-4e29-b75c-1f7977edf252'
        user_data.set_meta('result id', test_id)

        stop_called = {}

        def fake_stop(name, force):
            stop_called['name'] = name
            stop_called['force'] = force

        monkeypatch.setattr(running_tools, 'stop', fake_stop)

        runner = CliRunner()
        result = runner.invoke(stop_cli, ['cur'])
        assert result.exit_code == 0
        assert stop_called.get('name') == test_id

    def test_stop_with_non_id_name_calls_resolver(self, monkeypatch):
        """Line 19: non-UUID name triggers resolver.resolve_name."""
        resolved_id = '70ed01da-f291-4e29-b75c-1f7977edf252'

        # Use get_resolver() to avoid Python's name-mangling of __resolver inside
        # a class body (which would look for _TestStop__resolver instead).
        from commands import test_results
        resolver = test_results.get_resolver()
        monkeypatch.setattr(resolver, 'resolve_name', lambda n: resolved_id)

        stop_called = {}

        def fake_stop(name, force):
            stop_called['name'] = name
            stop_called['force'] = force

        monkeypatch.setattr(running_tools, 'stop', fake_stop)

        runner = CliRunner()
        result = runner.invoke(stop_cli, ['my-test-name'])
        assert result.exit_code == 0
        assert stop_called.get('name') == resolved_id
