import pytest
from types import SimpleNamespace
from click.testing import CliRunner
from commands.login import cli as login
from commands.status import cli as status

import sys

sys.path.append('neoload')


@pytest.fixture
def neoload_login():
    runner = CliRunner()
    runner.invoke(login, ['123456789fe70bf4a991ae6d8af62e21c4a00203abcdef'])
    print('\n@Before : %s' % str(runner.invoke(status).output))


@pytest.fixture
def valid_data():
    return SimpleNamespace(
        test_settings_id='75b63bc2-e75d-42ad-be3e-f712a69db723',
        test_result_id='843418dd-c24d-468a-a885-cab2c039f12a',
        test_result_id_to_delete = '184e0b68-eb4e-4368-9f6e-a56fd9c177cf'
    )


@pytest.fixture
def invalid_data():
    return SimpleNamespace(uuid='75b63bc2-1234-1234-abcd-f712a69db723')
