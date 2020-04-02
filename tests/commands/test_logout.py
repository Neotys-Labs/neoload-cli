import pytest
from click.testing import CliRunner
from commands.logout import cli as logout
from commands.status import cli as status


@pytest.mark.authentication
@pytest.mark.usefixtures("neoload_login")   # it's like @Before on the neoload_login function
def test_logout_basic():
    runner = CliRunner()
    result = runner.invoke(logout)
    assert result.exit_code == 0
    assert result.output == 'logout successfully\n'

    result = runner.invoke(status)
    assert result.exit_code == 0
    assert 'No settings is stored. Please use "neoload login" to start' in result.output

    # try again when already logged out
    result = runner.invoke(logout)
    assert result.exit_code == 0
    assert result.output == 'logout successfully\n'
