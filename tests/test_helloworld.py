from click.testing import CliRunner
from neoload.commands.login import cli as login

def test_hello_world():
  runner = CliRunner()
  result = runner.invoke(login, ['token'])
  assert result.exit_code == 0
  assert result.output == 'login successfully\n'