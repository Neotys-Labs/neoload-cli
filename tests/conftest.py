import pytest
from types import SimpleNamespace
from click.testing import CliRunner
from commands.login import cli as login


@pytest.fixture
def neoload_login():
    runner = CliRunner()
    result = runner.invoke(login, ['123456789fe70bf4a991ae6d8af62e21c4a00203abcdef'])
    print('\n@Before : %s' % str(result.output))


@pytest.fixture
def valid_data():
    return SimpleNamespace(
        test_id='75b63bc2-e75d-42ad-be3e-f712a69db723',
        test_result_id='75b63bc2-e75d-42ad-be3e-f712a69db723'
    )


@pytest.fixture
def invalid_data():
    return SimpleNamespace(uuid='75b63bc2-1234-1234-abcd-f712a69db723')
