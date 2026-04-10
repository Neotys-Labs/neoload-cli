"""
Tests for neoload_cli_lib/cli_exception.py

Missing lines (from coverage report): 13, 21, 26
  Line 13: CliException.__debug = boolean  (set_debug body)
  Line 21: __message = traceback.format_exc() + "\n\n" + __message  (debug branch in format_message)
  Line 26: return CliException.__debug  (is_debug body)
"""
import sys
import pytest

sys.path.append('neoload')

from neoload_cli_lib.cli_exception import CliException


class TestCliException:
    def setup_method(self):
        """Reset debug flag before each test."""
        CliException.set_debug(False)

    def teardown_method(self):
        """Reset debug flag after each test."""
        CliException.set_debug(False)

    # --- set_debug (line 13) ---

    def test_set_debug_true(self):
        CliException.set_debug(True)
        assert CliException.is_debug() is True

    def test_set_debug_false(self):
        CliException.set_debug(True)
        CliException.set_debug(False)
        assert CliException.is_debug() is False

    # --- is_debug (line 26) ---

    def test_is_debug_default_is_false(self):
        assert CliException.is_debug() is False

    def test_is_debug_returns_true_after_set(self):
        CliException.set_debug(True)
        assert CliException.is_debug() is True

    # --- format_message with debug=True (line 21) ---

    def test_format_message_without_debug(self):
        exc = CliException("something broke")
        msg = exc.format_message()
        assert "something broke" in msg
        # No traceback prefix expected when debug is False
        assert "Traceback" not in msg

    def test_format_message_with_debug_includes_traceback(self):
        CliException.set_debug(True)
        exc = CliException("debug message")
        msg = exc.format_message()
        # The message itself is always present
        assert "debug message" in msg
        # With debug=True, traceback.format_exc() is prepended (may be NoneType when no
        # active exception, but the code still runs through line 21)
        # The important thing is the line executed and the message is included.
        # format_exc() returns "NoneType: None\n" when there's no active exception.
        assert "\n\n" in msg

    def test_format_message_with_debug_during_exception(self):
        CliException.set_debug(True)
        try:
            raise ValueError("inner error")
        except ValueError:
            exc = CliException("outer message")
            msg = exc.format_message()
        assert "outer message" in msg
        assert "Traceback" in msg
        assert "ValueError" in msg

    # --- basic construction ---

    def test_exception_is_click_exception(self):
        import click
        exc = CliException("test error")
        assert isinstance(exc, click.ClickException)

    def test_message_stored(self):
        exc = CliException("stored message")
        assert exc.format_message() == "stored message"
