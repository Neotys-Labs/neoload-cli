from click.testing import CliRunner
from commands.logout import cli as logout


def test_logout_basic():
    runner = CliRunner()
    result = runner.invoke(logout)
    assert result.exit_code == 0
    assert result.output == 'logout successfully\n'
