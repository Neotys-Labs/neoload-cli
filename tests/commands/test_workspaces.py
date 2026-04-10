import pytest
from unittest.mock import MagicMock
from click.testing import CliRunner
from neoload_cli_lib import rest_crud, user_data, tools
from commands.workspaces import cli


MOCK_WORKSPACE_ID = '5e3acde2e860a132744ca916'


@pytest.mark.usefixtures("neoload_login")
class TestWorkspaces:

    def test_missing_command(self, monkeypatch):
        """Invoking without a command prints help message (lines 21-22)."""
        if monkeypatch is None:
            return
        # is_version_lower_than must return False so we don't hit the version guard
        monkeypatch.setattr(user_data, 'is_version_lower_than', lambda v: False)
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'command is mandatory' in result.output

    def test_version_too_low(self, monkeypatch):
        """When NeoLoad version < 2.5.0, prints error and returns (lines 24-25)."""
        if monkeypatch is None:
            return
        monkeypatch.setattr(user_data, 'is_version_lower_than', lambda v: True)
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert 'ERROR' in result.output
        assert '2.5.0' in result.output

    def test_ls_with_cur_alias(self, monkeypatch):
        """ls cur: resolves 'cur' to stored workspace id (line 28)."""
        if monkeypatch is None:
            return
        monkeypatch.setattr(user_data, 'is_version_lower_than', lambda v: False)
        monkeypatch.setattr(user_data, 'get_meta',
                            lambda key: MOCK_WORKSPACE_ID if key == 'workspace id' else None)
        ls_calls = []
        monkeypatch.setattr(tools, 'ls',
                            lambda name, is_id, resolver, filter_spec=None: ls_calls.append(filter_spec))
        runner = CliRunner()
        result = runner.invoke(cli, ['ls', 'cur'])
        assert result.exit_code == 0
        # filter_spec should have been built with the stored workspace id
        assert ls_calls, "tools.ls should have been called"
        assert MOCK_WORKSPACE_ID in (ls_calls[0] or '')

    def test_ls_no_filter(self, monkeypatch):
        """ls without name_or_id: calls tools.ls with no filter."""
        if monkeypatch is None:
            return
        monkeypatch.setattr(user_data, 'is_version_lower_than', lambda v: False)
        ls_calls = []
        monkeypatch.setattr(tools, 'ls',
                            lambda name, is_id, resolver, filter_spec=None: ls_calls.append(filter_spec))
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert ls_calls == [None]

    def test_ls_with_id_filter(self, monkeypatch):
        """ls <id>: builds a filter_spec with the given id."""
        if monkeypatch is None:
            return
        monkeypatch.setattr(user_data, 'is_version_lower_than', lambda v: False)
        ls_calls = []
        monkeypatch.setattr(tools, 'ls',
                            lambda name, is_id, resolver, filter_spec=None: ls_calls.append(filter_spec))
        runner = CliRunner()
        result = runner.invoke(cli, ['ls', MOCK_WORKSPACE_ID])
        assert result.exit_code == 0
        assert ls_calls, "tools.ls should have been called"
        assert MOCK_WORKSPACE_ID in (ls_calls[0] or '')

    def test_use_command(self, monkeypatch):
        """use <id>: calls tools.get_id then tools.use."""
        if monkeypatch is None:
            return
        monkeypatch.setattr(user_data, 'is_version_lower_than', lambda v: False)
        monkeypatch.setattr(tools, 'get_id',
                            lambda name, resolver, is_id: MOCK_WORKSPACE_ID)
        use_calls = []
        monkeypatch.setattr(tools, 'use',
                            lambda id_, meta_key, resolver: use_calls.append(id_))
        runner = CliRunner()
        result = runner.invoke(cli, ['use', MOCK_WORKSPACE_ID])
        assert result.exit_code == 0
        assert use_calls == [MOCK_WORKSPACE_ID]
