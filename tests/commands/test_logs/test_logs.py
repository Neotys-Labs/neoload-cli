import pytest
from datetime import datetime
from neoload_cli_lib import rest_crud
from commands import test_results
from neoload_cli_lib.logs_tools import display_logs, format_time
from neoload_cli_lib.logs_traduction_map import dicotrad

@pytest.fixture
def mock_response(monkeypatch):
    def mock_get(url):
        return [
            {'timestamp': 1625247600000, 'content': 'Test log entry 1'},
            {'timestamp': 1625247601000, 'content': 'Test log entry 2'},
            {'timestamp': 1625247602000, 'content': 'AUTO_RESERVE'}
        ]

    monkeypatch.setattr(rest_crud, 'get', mock_get)

@pytest.mark.usefixtures("mock_response", "neoload_login")
def test_display_logs(capfd):
    displayed_lines = []
    results_id = "test_results_id"

    display_logs(displayed_lines, results_id)

    captured = capfd.readouterr()
    output = captured.out.strip().split("\n")

    expected_logs = [
        f"{format_time(1625247600000)} Test log entry 1",
        f"{format_time(1625247601000)} Test log entry 2",
        f"{format_time(1625247602000)} Auto reserve resources"
    ]

    assert output == expected_logs, f"Expected {expected_logs} but got {output}"

def test_format_time():
    timestamp = 1625247600000
    formatted_time = format_time(timestamp)
    assert formatted_time == "02.07.21 07:40:00 PM", f"Expected '02.07.21 07:40:00 PM' but got {formatted_time}"

def test_dicotrad():
    assert dicotrad['AUTO_RESERVE'] == "Auto reserve resources", f"Expected 'Auto reserve resources' but got {dicotrad['AUTO_RESERVE']}"
