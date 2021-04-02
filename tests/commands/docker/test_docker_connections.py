import pytest
import os
from click.testing import CliRunner
from commands.login import cli as login
from commands.status import cli as status
from commands.docker import cli as docker
from neoload_cli_lib import docker_lib
from helpers.test_utils import *
import json
import tempfile

@pytest.mark.docker
@pytest.mark.slow
@pytest.mark.makelivecalls
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestDockerConnections:
    def test_docker_status(self):
        runner = CliRunner()
        result = runner.invoke(docker, ['status'])
        assert_success(result)
        assert docker_lib.DOCKER_CONTROLLER_IMAGE in result.output, "Could not find indicators of successful connection to Docker environment"

    def test_docker_up_and_down(self):
        runner = CliRunner()
        last_err = None
        up_happened = False
        down_happened = False
        try:
            result = runner.invoke(docker, ['up'])
            assert_success(result)
            up_happened = True
        except Exception as err:
            last_err = err

        try:
            # always try, even if for simply to clean up
            result = runner.invoke(docker, ['down'])
            if up_happened:
                assert_success(result)
                down_happened = True
        except:
            last_err = err

        assert up_happened, "Could not run the docker UP command: {}".format("" if last_err is none else str(last_err))
        assert down_happened, "Could not run the docker DOWN command: {}".format("" if last_err is none else str(last_err))
