"""
Tests for neoload/version_manager.py

The file has just 4 lines:
  1: try:
  2:     from version import __version__
  3: except ImportError as e:
  4:     __version__ = None

Lines 3-4 are the ImportError handler path that executes when the `version`
module is not installed (typical dev environment without a built package).
The existing coverage already covers lines 1-2 OR lines 3-4 depending on the
environment. We need to cover whichever branch is missing.

Since in CI/dev the `version` module is absent, lines 3-4 execute and lines
1-2 are the "missing" side.  We cover both branches by:
  - importing the module normally (covers whichever path runs in this env)
  - forcing the ImportError path via sys.modules manipulation
"""
import sys
import types
import importlib
import pytest


class TestVersionManager:
    def test_import_succeeds(self):
        """Importing version_manager should never raise."""
        # Remove cached module so we get a fresh import
        sys.modules.pop('neoload.version_manager', None)
        sys.modules.pop('version_manager', None)

        sys.path.insert(0, 'neoload')
        try:
            import version_manager
            # __version__ is either a string or None — both are valid
            assert version_manager.__version__ is None or isinstance(version_manager.__version__, str)
        finally:
            sys.path.pop(0)

    def test_version_none_when_version_module_missing(self, monkeypatch):
        """Covers lines 3-4: the ImportError branch sets __version__ = None."""
        # Make 'version' unimportable
        monkeypatch.setitem(sys.modules, 'version', None)

        # Force reload of version_manager
        sys.modules.pop('version_manager', None)
        sys.modules.pop('neoload.version_manager', None)

        sys.path.insert(0, 'neoload')
        try:
            import version_manager
            importlib.reload(version_manager)
            assert version_manager.__version__ is None
        finally:
            sys.path.pop(0)
            sys.modules.pop('version_manager', None)

    def test_version_string_when_version_module_present(self, monkeypatch):
        """Covers lines 1-2: the happy path where version module exists."""
        fake_version = types.ModuleType('version')
        fake_version.__version__ = '9.9.9'
        monkeypatch.setitem(sys.modules, 'version', fake_version)

        # Force reload of version_manager so it re-executes the try block
        sys.modules.pop('version_manager', None)
        sys.modules.pop('neoload.version_manager', None)

        sys.path.insert(0, 'neoload')
        try:
            import version_manager
            importlib.reload(version_manager)
            assert version_manager.__version__ == '9.9.9'
        finally:
            sys.path.pop(0)
            sys.modules.pop('version_manager', None)
