import os

from neoload_cli_lib import tools


def mock_get_env(mock_values: dict, var: str, default: str = None):
    return mock_values.get(var, default)


class TestTools:
    def test_is_user_interactive(self, monkeypatch):
        mocks = {}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is False

        mocks = {'NL_INTERACTIVE': 'some value'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is False

        mocks = {'NL_INTERACTIVE': 'false'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is False

        mocks = {'NL_INTERACTIVE': 'False'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is False

        mocks = {'NL_INTERACTIVE': '0'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is False

        mocks = {'NL_INTERACTIVE': '1'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is True

        mocks = {'NL_INTERACTIVE': 'True'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is True

        mocks = {'NL_INTERACTIVE': 'trUe'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is True

        mocks = {'NL_INTERACTIVE': 'yes'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is True

        mocks = {'NL_INTERACTIVE': 'yEs'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is True

        mocks = {'NL_INTERACTIVE': 'Y'}
        monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
        assert tools.is_user_interactive() is True

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
