"""
Tests for neoload_cli_lib/hooks.py

Coverage targets (lines missing before these tests):
  9-20  : trig() body — module import traversal and function call
  36    : unregister() else branch when hook list becomes empty after removal
  42-43 : is_registered()
"""
import pytest
from neoload_cli_lib import hooks, config_global


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clear_hook(name):
    """Remove a hook key from config_global so tests start clean."""
    config_global.set_attr('$hooks.' + name, None)


# ---------------------------------------------------------------------------
# Tests for register() — also exercises the hook storage layer
# ---------------------------------------------------------------------------

class TestRegister:
    def setup_method(self):
        _clear_hook('test_event')

    def test_register_adds_function_to_hook(self):
        hooks.register('test_event', 'mymodule.myfunc')
        hook = config_global.get_attr('$hooks.test_event')
        assert 'mymodule.myfunc' in hook

    def test_register_preserves_existing_functions(self):
        hooks.register('test_event', 'mymodule.func_a')
        hooks.register('test_event', 'mymodule.func_b')
        hook = config_global.get_attr('$hooks.test_event')
        assert 'mymodule.func_a' in hook
        assert 'mymodule.func_b' in hook

    def test_register_no_duplicates(self):
        hooks.register('test_event', 'mymodule.myfunc')
        hooks.register('test_event', 'mymodule.myfunc')
        hook = config_global.get_attr('$hooks.test_event')
        assert hook.count('mymodule.myfunc') == 1


# ---------------------------------------------------------------------------
# Tests for unregister() — including the else branch (line 36-38)
# ---------------------------------------------------------------------------

class TestUnregister:
    def setup_method(self):
        _clear_hook('test_event')

    def test_unregister_removes_function(self):
        hooks.register('test_event', 'mymodule.func_a')
        hooks.register('test_event', 'mymodule.func_b')
        hooks.unregister('test_event', 'mymodule.func_a')
        hook = config_global.get_attr('$hooks.test_event')
        assert 'mymodule.func_a' not in hook
        assert 'mymodule.func_b' in hook

    def test_unregister_last_function_sets_none(self):
        """When the last function is removed the hook list becomes empty →
        the else branch (line 38) sets the attr to None."""
        hooks.register('test_event', 'mymodule.only_func')
        hooks.unregister('test_event', 'mymodule.only_func')
        hook = config_global.get_attr('$hooks.test_event')
        assert not hook  # None or empty list

    def test_unregister_noop_when_hook_not_registered(self):
        """Calling unregister when hook key is absent should not raise."""
        _clear_hook('test_event')
        # Should silently do nothing — no hook exists yet
        hooks.unregister('test_event', 'mymodule.myfunc')


# ---------------------------------------------------------------------------
# Tests for is_registered() (lines 42-43)
# ---------------------------------------------------------------------------

class TestIsRegistered:
    def setup_method(self):
        _clear_hook('test_event')

    def test_is_registered_returns_true_when_registered(self):
        hooks.register('test_event', 'mymodule.myfunc')
        assert hooks.is_registered('test_event', 'mymodule.myfunc') is True

    def test_is_registered_returns_falsy_when_not_registered(self):
        # is_registered returns None (falsy) when the hook key doesn't exist
        assert not hooks.is_registered('test_event', 'mymodule.myfunc')

    def test_is_registered_returns_falsy_after_unregister(self):
        hooks.register('test_event', 'mymodule.myfunc')
        hooks.unregister('test_event', 'mymodule.myfunc')
        # After unregistering the last entry the hook is None → falsy
        assert not hooks.is_registered('test_event', 'mymodule.myfunc')

    def test_is_registered_distinguishes_different_functions(self):
        hooks.register('test_event', 'mymodule.func_a')
        assert hooks.is_registered('test_event', 'mymodule.func_a') is True
        assert hooks.is_registered('test_event', 'mymodule.func_b') is False


# ---------------------------------------------------------------------------
# Tests for trig() (lines 9-20) — module import traversal and invocation
# ---------------------------------------------------------------------------

class TestTrig:
    def setup_method(self):
        _clear_hook('test_event')

    def test_trig_calls_registered_function(self, monkeypatch):
        """trig() must import the module, walk the dotted path, and call the leaf."""
        if monkeypatch is None:
            return

        # We register a real importable function: 'os.path.join'
        # trig() will do: __import__('os'), getattr(module,'path'), getattr(module,'join'), call it
        hooks.register('test_event', 'os.path.join')

        # Intercept the actual call so we can assert it was reached.
        called_with = []

        import os.path as osp
        original_join = osp.join

        def fake_join(*args, **kwargs):
            called_with.append(args)
            return original_join(*args, **kwargs)

        monkeypatch.setattr('os.path.join', fake_join)
        hooks.trig('test_event', 'a', 'b')
        assert len(called_with) == 1
        assert called_with[0] == ('a', 'b')

    def test_trig_noop_when_no_hook_registered(self):
        """trig() with no registered hook should silently do nothing."""
        _clear_hook('empty_event')
        # Must not raise
        hooks.trig('empty_event', 'arg1')

    def test_trig_calls_multiple_registered_functions(self, monkeypatch):
        """All registered functions are invoked."""
        if monkeypatch is None:
            return

        call_log = []

        # Use two different real importable callables whose calls we can track
        import os
        monkeypatch.setattr(os, 'getcwd', lambda: call_log.append('getcwd') or '/fake')
        monkeypatch.setattr(os, 'getpid', lambda: call_log.append('getpid') or 0)

        hooks.register('test_event', 'os.getcwd')
        hooks.register('test_event', 'os.getpid')
        hooks.trig('test_event')

        assert 'getcwd' in call_log
        assert 'getpid' in call_log

    def test_trig_explicit_submodule_import(self):
        """Cover lines 17-18: the __import__ fallback in trig() when
        getattr(module, comp, None) returns None for a sub-package component.

        trig() walks a dotted path by calling getattr on successive module objects.
        When a component is missing as an attribute (None), it calls __import__ on
        the dotted path built so far, then retries getattr. We exercise this by:
          1. Building a fake package 'fakepkg' whose top-level module does NOT have
             'sub' as an attribute yet.
          2. Intercepting builtins.__import__ so that when trig() calls
             __import__('fakepkg.sub'), we manually attach 'sub' to 'fakepkg' and
             register it in sys.modules — exactly what a real import would do.
        """
        import sys
        import builtins
        from types import ModuleType

        _clear_hook('test_event')
        called_args = []

        # Build a minimal fake package hierarchy
        fakepkg = ModuleType('fakepkg')
        fakesub = ModuleType('fakepkg.sub')
        fakesub.myfunc = lambda *a, **kw: called_args.append(a)

        # Register only the top-level package; 'sub' is NOT an attribute yet
        sys.modules['fakepkg'] = fakepkg

        original_import = builtins.__import__

        def patched_import(name, *args, **kwargs):
            if name == 'fakepkg.sub':
                # Simulate real import: attach 'sub' to parent and add to sys.modules
                fakepkg.sub = fakesub
                sys.modules['fakepkg.sub'] = fakesub
                return fakepkg
            return original_import(name, *args, **kwargs)

        builtins.__import__ = patched_import
        try:
            hooks.register('test_event', 'fakepkg.sub.myfunc')
            hooks.trig('test_event', 'arg1', 'arg2')
            assert len(called_args) == 1
            assert called_args[0] == ('arg1', 'arg2')
        finally:
            builtins.__import__ = original_import
            sys.modules.pop('fakepkg', None)
            sys.modules.pop('fakepkg.sub', None)
            _clear_hook('test_event')
