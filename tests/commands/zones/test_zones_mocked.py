"""Mocked unit tests for neoload/commands/zones.py — covers lines missed by live-call tests."""
import json
import sys
import pytest
from click.testing import CliRunner

sys.path.append('neoload')
from commands.zones import cli as zones, filter_result, get_end_point, display_human_sub, print_human
from neoload_cli_lib import rest_crud


# ---------------------------------------------------------------------------
# Sample zone fixture used across tests
# ---------------------------------------------------------------------------

_ZONE_STATIC = {
    "id": "zone-static-1",
    "name": "Static Zone One",
    "type": "STATIC",
    "controllers": [
        {"name": "ctrl-a", "version": "7.10", "status": "AVAILABLE"}
    ],
    "loadgenerators": [
        {"name": "lg-a", "version": "7.10", "status": "AVAILABLE"},
        {"name": "lg-b", "version": "7.10", "status": "UNAVAILABLE"},
    ],
}

_ZONE_DYNAMIC = {
    "id": "zone-dyn-1",
    "name": "Dynamic Zone One",
    "type": "DYNAMIC",
    "controllers": [],
    "loadgenerators": [],
}


# ---------------------------------------------------------------------------
# filter_result unit tests (pure Python, no HTTP)
# ---------------------------------------------------------------------------

class TestFilterResult:
    def test_no_filters_passes_all(self):
        assert filter_result(_ZONE_STATIC, None, None) is True
        assert filter_result(_ZONE_DYNAMIC, None, None) is True

    def test_static_filter_passes_static_zone(self):
        # static=True → keep STATIC zones
        assert filter_result(_ZONE_STATIC, None, True) is True

    def test_static_filter_rejects_dynamic_zone(self):
        assert filter_result(_ZONE_DYNAMIC, None, True) is False

    def test_dynamic_filter_passes_dynamic_zone(self):
        # static=False → keep DYNAMIC zones
        assert filter_result(_ZONE_DYNAMIC, None, False) is True

    def test_dynamic_filter_rejects_static_zone(self):
        assert filter_result(_ZONE_STATIC, None, False) is False

    def test_name_filter_matches_name(self):
        assert filter_result(_ZONE_STATIC, "Static Zone One", None) is True

    def test_name_filter_matches_id(self):
        assert filter_result(_ZONE_STATIC, "zone-static-1", None) is True

    def test_name_filter_rejects_non_match(self):
        assert filter_result(_ZONE_STATIC, "non-existent", None) is False

    def test_combined_static_and_name_match(self):
        assert filter_result(_ZONE_STATIC, "zone-static-1", True) is True

    def test_combined_static_and_name_mismatch_type(self):
        # dynamic zone filtered by static=True → rejected by type before name check
        assert filter_result(_ZONE_DYNAMIC, "zone-dyn-1", True) is False

    def test_combined_dynamic_and_name_match(self):
        assert filter_result(_ZONE_DYNAMIC, "zone-dyn-1", False) is True


# ---------------------------------------------------------------------------
# get_end_point unit tests
# ---------------------------------------------------------------------------

class TestGetEndPoint:
    def test_without_id(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import rest_crud
        monkeypatch.setattr(rest_crud, 'base_endpoint', lambda: 'v3')
        ep = get_end_point()
        assert ep.endswith("/resources/zones")

    def test_with_id(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import rest_crud
        monkeypatch.setattr(rest_crud, 'base_endpoint', lambda: 'v3')
        ep = get_end_point("myzoneid")
        assert ep.endswith("/resources/zones/myzoneid")


# ---------------------------------------------------------------------------
# CLI integration tests with mocked HTTP
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("neoload_login")
class TestZonesCLIMocked:

    def _mock_get(self, monkeypatch, zones_list):
        """Make rest_crud.get return zones_list for any endpoint."""
        monkeypatch.setattr(rest_crud, 'get', lambda ep: zones_list)
        monkeypatch.setattr(rest_crud, 'set_current_command', lambda: None)

    def test_list_all_mocked(self, monkeypatch):
        if monkeypatch is None:
            return
        self._mock_get(monkeypatch, [_ZONE_STATIC, _ZONE_DYNAMIC])
        runner = CliRunner()
        result = runner.invoke(zones, [])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert len(data) == 2

    def test_list_filter_by_name(self, monkeypatch):
        if monkeypatch is None:
            return
        self._mock_get(monkeypatch, [_ZONE_STATIC, _ZONE_DYNAMIC])
        runner = CliRunner()
        result = runner.invoke(zones, ["Static Zone One"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["id"] == "zone-static-1"

    def test_list_filter_by_id(self, monkeypatch):
        if monkeypatch is None:
            return
        self._mock_get(monkeypatch, [_ZONE_STATIC, _ZONE_DYNAMIC])
        runner = CliRunner()
        result = runner.invoke(zones, ["zone-dyn-1"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["type"] == "DYNAMIC"

    def test_list_static_flag(self, monkeypatch):
        if monkeypatch is None:
            return
        self._mock_get(monkeypatch, [_ZONE_STATIC, _ZONE_DYNAMIC])
        runner = CliRunner()
        result = runner.invoke(zones, ["--static"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert all(z["type"] == "STATIC" for z in data)

    def test_list_dynamic_flag(self, monkeypatch):
        if monkeypatch is None:
            return
        self._mock_get(monkeypatch, [_ZONE_STATIC, _ZONE_DYNAMIC])
        runner = CliRunner()
        result = runner.invoke(zones, ["--dynamic"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert all(z["type"] == "DYNAMIC" for z in data)

    def test_list_human_output(self, monkeypatch):
        if monkeypatch is None:
            return
        self._mock_get(monkeypatch, [_ZONE_STATIC])
        runner = CliRunner()
        result = runner.invoke(zones, ["-h"])
        assert result.exit_code == 0, result.output
        assert "TYPE\tID\tNAME" in result.output
        assert "Controllers (1)" in result.output
        assert "Load Generator (2)" in result.output
        assert "ctrl-a" in result.output
        assert "lg-a" in result.output

    def test_list_empty_result(self, monkeypatch):
        if monkeypatch is None:
            return
        self._mock_get(monkeypatch, [])
        runner = CliRunner()
        result = runner.invoke(zones, [])
        assert result.exit_code == 0, result.output
        assert json.loads(result.output) == []

    def test_human_with_name_filter_no_match(self, monkeypatch):
        if monkeypatch is None:
            return
        self._mock_get(monkeypatch, [_ZONE_STATIC, _ZONE_DYNAMIC])
        runner = CliRunner()
        result = runner.invoke(zones, ["-h", "nonexistent"])
        assert result.exit_code == 0, result.output
        # Only the header should be printed, no zone rows
        assert "TYPE\tID\tNAME" in result.output
        assert "zone-static-1" not in result.output


# ---------------------------------------------------------------------------
# print_human / display_human_sub unit tests
# ---------------------------------------------------------------------------

class TestPrintHuman:
    def test_display_human_sub_empty(self, capsys):
        display_human_sub([], "Controllers")
        captured = capsys.readouterr()
        assert "Controllers (0)" in captured.out

    def test_display_human_sub_with_elements(self, capsys):
        elements = [{"name": "ctrl-x", "version": "8.0", "status": "AVAILABLE"}]
        display_human_sub(elements, "Controllers")
        captured = capsys.readouterr()
        assert "Controllers (1)" in captured.out
        assert "ctrl-x" in captured.out
        assert "8.0" in captured.out
        assert "AVAILABLE" in captured.out

    def test_print_human_renders_all_sections(self, capsys):
        zones_list = [_ZONE_STATIC]
        print_human(zones_list)
        captured = capsys.readouterr()
        assert "TYPE\tID\tNAME" in captured.out
        assert "STATIC\tzone-static-1\tStatic Zone One" in captured.out
        assert "Controllers (1)" in captured.out
        assert "Load Generator (2)" in captured.out

    def test_print_human_empty_controllers_and_lgs(self, capsys):
        zone = {
            "id": "z1", "name": "Empty Zone", "type": "STATIC",
            "controllers": [], "loadgenerators": []
        }
        print_human([zone])
        captured = capsys.readouterr()
        assert "Controllers (0)" in captured.out
        assert "Load Generator (0)" in captured.out
