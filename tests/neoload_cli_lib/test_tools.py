import os
import sys

from neoload_cli_lib import tools


def mock_get_env(mock_values: dict, var: str, default: str = None):
    return mock_values.get(var, default)


class TestTools:
    def test_are_any_ci_env_vars_active(self, monkeypatch):
        mocks = {}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.are_any_ci_env_vars_active() is False

        mocks = {'TRAVIS': 'some value'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.are_any_ci_env_vars_active() is True

        mocks = {'TRAVIS': 'false'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.are_any_ci_env_vars_active() is False

        mocks = {'TRAVIS': 'False'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.are_any_ci_env_vars_active() is False

        mocks = {'TRAVIS': '0'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.are_any_ci_env_vars_active() is False

        mocks = {'TRAVIS': '1'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.are_any_ci_env_vars_active() is True

        mocks = {'TRAVIS': 'True'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.are_any_ci_env_vars_active() is True

    def test_is_user_interactive_tty_false(self, monkeypatch):
        monkeypatch.setattr(sys.__stdin__, 'isatty', lambda: False)
        mocks = {}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is False

        mocks = {'TRAVIS': 'True'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is False
        mocks = {'NL_INTERACTIVE': '1', 'TRAVIS': 'True'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is True

        mocks = {'NL_INTERACTIVE': '0', 'TRAVIS': 'True'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is False

        mocks = {'NL_INTERACTIVE': '1', 'TRAVIS': '0'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is True

        mocks = {'NL_INTERACTIVE': '0', 'TRAVIS': '0'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is False

    def test_is_user_interactive_tty_true(self, monkeypatch):
        monkeypatch.setattr(sys.__stdin__, 'isatty', lambda: True)
        mocks = {}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is True

        mocks = {'TRAVIS': 'True'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is False

        mocks = {'NL_INTERACTIVE': '1', 'TRAVIS': 'True'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is True

        mocks = {'NL_INTERACTIVE': '0', 'TRAVIS': 'True'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is False

        mocks = {'NL_INTERACTIVE': '1', 'TRAVIS': '0'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is True

        mocks = {'NL_INTERACTIVE': '0', 'TRAVIS': '0'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is False

    def test_is_environment_var_true(self, monkeypatch):
        mocks = {}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_true('var') is False

        mocks = {'var': '0'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_true('var') is False

        mocks = {'var': 'some value'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_false('var') is False

        mocks = {'var': '1'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_true('var') is True

        mocks = {'var': 'y'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_true('var') is True

        mocks = {'var': 'yes'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_true('var') is True

        mocks = {'var': 'tRUe'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_true('var') is True

    def test_is_environment_var_false(self, monkeypatch):
        mocks = {}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_false('var') is False

        mocks = {'var': '1'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_false('var') is False

        mocks = {'var': 'some value'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_false('var') is False

        mocks = {'var': '0'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_false('var') is True

        mocks = {'var': 'n'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_false('var') is True

        mocks = {'var': 'no'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_false('var') is True

        mocks = {'var': 'fALse'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_environment_var_false('var') is True
