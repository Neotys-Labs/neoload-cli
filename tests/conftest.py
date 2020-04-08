import pytest
from types import SimpleNamespace
from click.testing import CliRunner
from commands.login import cli as login
from commands.status import cli as status

import sys

sys.path.append('neoload')
__default_random_token = '12345678912345678901ae6d8af6abcdefabcdefabcdef'
__default_api_url = 'https://neoload-api.saas.neotys.com/'


def pytest_addoption(parser):
    parser.addoption('--token', action='store', default=__default_random_token)
    parser.addoption('--url', action='store', default=__default_api_url)


@pytest.fixture
def neoload_login(request):
    token = request.config.getoption('--token')
    api_url = request.config.getoption('--url')
    runner = CliRunner()
    runner.invoke(login, [token, '--url', api_url])
    print('\n@Before : %s' % str(runner.invoke(status).output))


@pytest.fixture
def valid_data():
    return SimpleNamespace(
        test_settings_id='1d4e9fe5-3daf-4ac9-8283-d04e2a97ed5e',
        test_result_id='2f70e200-d11b-4e6b-96b2-e396cc18e3e3',
        test_result_id_to_delete = '843418dd-c24d-468a-a885-cab2c039f12a'
    )


@pytest.fixture
def invalid_data():
    return SimpleNamespace(uuid='75b63bc2-1234-1234-abcd-f712a69db723')


@pytest.fixture
def monkeypatch(request, monkeypatch):
    token = request.config.getoption('--token')
    # Disable mocks when a specific token is provided
    return monkeypatch if token is __default_random_token else None
