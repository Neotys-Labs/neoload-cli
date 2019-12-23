import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))

skipmarkers = [
    "slow",
    "slas",
    "profiles",
    "queries",
    "files"
]
#TODO: figure out how to present the last line of stdout from 'neoload' to test step (after step name)
#https://pythontesting.net/framework/pytest/pytest-logging-real-time/

def pytest_addoption(parser):
    parser.addoption(
        "--skipall", action="store_true", default=False, help="skips all tests...except those specified with --only[category]"
    )
    for m in skipmarkers:
        parser.addoption(
            "--skip"+m, action="store_true", default=False, help="skips "+m+" tests"
        )
        parser.addoption(
            "--only"+m, action="store_true", default=False, help="only run "+m+" tests"
        )

def pytest_configure(config):
    for m in skipmarkers:
        config.addinivalue_line("markers", m+": mark test as "+m+" to run")


def pytest_collection_modifyitems(config, items):

    skip = pytest.mark.skip(reason="need option to run")

    for item in items:
        if any(filter(lambda m: config.getoption("--only"+m), skipmarkers)):
            for m in skipmarkers:
                if m in item.keywords and not config.getoption("--only"+m):
                    item.add_marker(skip)
        else:
            for m in skipmarkers:
                if m in item.keywords and config.getoption("--skip"+m):
                    item.add_marker(skip)
