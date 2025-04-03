import datetime
import os
import time

import pytest
from types import SimpleNamespace
from _pytest.main import Session
from click.testing import CliRunner

import sys
sys.path.append('neoload')

from commands.login import cli as login
from commands.status import cli as status
from commands.config import cli as config
from tests.helpers.test_utils import mock_login_get_urls


__default_random_token = '12345678912345678901ae6d8af6abcdefabcdefabcdef'
__default_api_url = 'https://neoload-api.saas.neotys.com'

# set the testing timezone to US/Pacific
os.environ['TZ'] = 'Europe/Paris'
try:
    from time import tzset
    time.tzset()
except ImportError:
    print("usecurentlocal")
FAKE_NOW_DATETIME = datetime.datetime(2023, 12, 25, 17, 5, 55)


def pytest_addoption(parser):
    parser.addoption('--token', action='store', default=__default_random_token)
    parser.addoption('--url', action='store', default=__default_api_url)
    parser.addoption('--workspace', action='store', default=None)
    parser.addoption('--makelivecalls', action='store_true')


def pytest_configure(config):
    if not config.option.makelivecalls:
        setattr(config.option, 'markexpr', 'not makelivecalls')


def pytest_sessionstart(session: Session):
    """
    Called after the Session object has been created
    and before performing collection and entering the run test loop.
    The test suite needs to start already logged in, because during the class initialization
    of the commands, the function base_endpoint_with_workspace() throw an exception if not logged in.
    """
    CliRunner().invoke(config, ["set", "status.resolvenames=False"])
    CliRunner().invoke(login, ["xxxxx", '--url', "bad_url"])


@pytest.fixture
def neoload_login(request, monkeypatch):
    token = request.config.getoption('--token')
    api_url = request.config.getoption('--url')
    workspace = request.config.getoption('--workspace')

    makelivecalls = request.config.getoption('--makelivecalls')
    if makelivecalls:
        CliRunner().invoke(config, ["set", "status.resolvenames=True"])
        CliRunner().invoke(config, ["set", "docker.zone=kcNc7"])

    runner = CliRunner()
    result_status = runner.invoke(status)
    # do login if not already logged-in with the right credentials
    if "aren't logged in" in result_status.output \
            or "No settings is stored" in result_status.output \
            or api_url not in result_status.output \
            or '*' * (len(token) - 3) + token[-3:] not in result_status.output:
        mock_login_get_urls(monkeypatch, 'SaaS')
        cli_options = [token, '--url', api_url]
        if workspace and len(workspace) > 0:
            cli_options.extend(['--workspace', workspace])
        runner.invoke(login, cli_options)
    else:
        print('\n@Before : Already logged on %s' % api_url)


@pytest.fixture
def valid_data():
    return SimpleNamespace(
        test_settings_id='2e4fb86c-ac70-459d-a452-8fa2e9101d16',
        test_result_id='184e0b68-eb4e-4368-9f6e-a56fd9c177cf',
        test_result_id_to_delete='07040512-23ca-4d9c-bdb7-a64450ea5949',
        default_workspace_id='5e3acde2e860a132744ca916'
    )


@pytest.fixture
def invalid_data():
    return SimpleNamespace(uuid='75b63bc2-1234-1234-abcd-f712a69db723')


@pytest.fixture
def monkeypatch(request, monkeypatch):
    token = request.config.getoption('--token')
    # Disable mocks when a specific token is provided
    return monkeypatch if token is __default_random_token else None


@pytest.fixture
def patch_datetime_now(monkeypatch):

    class MyDatetime(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return FAKE_NOW_DATETIME

        @classmethod
        def now(cls, tz=None):
            return FAKE_NOW_DATETIME

        @classmethod
        def today(cls):
            return FAKE_NOW_DATETIME

    monkeypatch.setattr(datetime, 'datetime', MyDatetime)
