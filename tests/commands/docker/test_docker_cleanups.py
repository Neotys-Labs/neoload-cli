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
class TestDockerCleanups:
    def test_docker_clean(self):
        runner = CliRunner()
        result = runner.invoke(docker, ['clean'])
        assert_success(result)

    def test_docker_forget(self):
        runner = CliRunner()
        result = runner.invoke(docker, ['forget'])
        assert_success(result)
