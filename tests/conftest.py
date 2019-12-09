import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))

#TODO: figure out how to present the last line of stdout from 'neoload' to test step (after step name)
#https://pythontesting.net/framework/pytest/pytest-logging-real-time/

def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--xrunslow", action="store_true", default=False, help="ignores 'run slow tests' temporarily"
    )

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
