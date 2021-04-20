import pytest
import os
from click.testing import CliRunner
from commands.login import cli as login
from commands.status import cli as status
from commands.docker import cli as docker
from neoload_cli_lib import docker_lib
from tests.helpers.test_utils import *
import json
import tempfile

@pytest.mark.docker
@pytest.mark.slow
@pytest.mark.makelivecalls
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestDockerHooks:
    def test_docker_install(self):
        runner = CliRunner()
        result = runner.invoke(docker, ['install'])
        assert_success(result)
        result = runner.invoke(docker, ['status'])
        assert_success(result)
        assert 'docker hooks is installed', "Could not verify that docker hooks is installed"

    def test_docker_uninstall(self):
        runner = CliRunner()
        result = runner.invoke(docker, ['uninstall'])
        assert_success(result)
        result = runner.invoke(docker, ['status'])
        assert_success(result)
        assert 'docker hooks is not installed', "Could not verify that docker hooks is uninstalled"
