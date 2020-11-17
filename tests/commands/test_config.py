from click.testing import CliRunner

from commands.config import cli as config
from neoload_cli_lib.config_global import __config_file
import os


def test_config_basic():
    if os.path.exists(__config_file):
        os.unlink(__config_file)

    runner = CliRunner()
    result = runner.invoke(config, ["set", "toto=titi"])
    assert result.exit_code == 0

    result = runner.invoke(config, ["set", "test=y"])
    assert result.exit_code == 0

    result = runner.invoke(config, ["ls"])
    assert result.exit_code == 0
    assert 'toto = titi' in result.output
    assert 'test = True' in result.output

    result = runner.invoke(config, ["set", "toto="])
    assert result.exit_code == 0

    result = runner.invoke(config, ["ls"])
    assert result.exit_code == 0
    assert 'toto' not in result.output
    assert 'test = True' in result.output

    os.unlink(__config_file)

