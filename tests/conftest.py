import pytest
from types import SimpleNamespace
from click.testing import CliRunner
from commands.login import cli as login
from commands.status import cli as status

import sys
import os

sys.path.append('neoload')
__default_random_token = '12345678912345678901ae6d8af6abcdefabcdefabcdef'
__default_api_url = 'https://neoload-api.saas.neotys.com/'


def pytest_addoption(parser):
    parser.addoption('--integration', action='store_true', dest="integration",
                 default=False, help="enable integration tests that use a live system; $NLW_TOKEN and $NLW_URL")
    parser.addoption('--token', action='store', default=__default_random_token)
    parser.addoption('--url', action='store', default=__default_api_url)

def pytest_configure(config):
    if not config.option.integration:
        setattr(config.option, 'markexpr', 'not integration')

@pytest.fixture
def neoload_login(request, monkeypatch):
    token = request.config.getoption('--token')
    api_url = request.config.getoption('--url')
    runner = CliRunner()
    result_status = runner.invoke(status)

    if request.config.option.integration:
        if token == __default_random_token or len(("" if token is None else str(token))) < 1: token = os.getenv('NLW_TOKEN')
        if api_url == __default_api_url or len(("" if api_url is None else str(api_url))) < 1: api_url = os.getenv('NLW_URL')

    # do login if not already logged-in with the right credentials
    if "aren't logged in" in result_status.output \
            or api_url not in result_status.output \
            or '*' * (len(token) - 3) + token[-3:] not in result_status.output:
        runner.invoke(login, [token, '--url', api_url])
        print('\n@Before : %s' % str(runner.invoke(status).output))
    else:
        print('\n@Before : Already logged on %s' % api_url)


@pytest.fixture
def valid_data():
    return SimpleNamespace(
        test_settings_id='2e4fb86c-ac70-459d-a452-8fa2e9101d16',
        test_result_id='184e0b68-eb4e-4368-9f6e-a56fd9c177cf',
        test_result_id_to_delete = '07040512-23ca-4d9c-bdb7-a64450ea5949'
    )


@pytest.fixture
def invalid_data():
    return SimpleNamespace(uuid='75b63bc2-1234-1234-abcd-f712a69db723')


@pytest.fixture
def monkeypatch(request, monkeypatch):
    token = request.config.getoption('--token')
    # Disable mocks when a specific token is provided
    return monkeypatch if token is __default_random_token else None
