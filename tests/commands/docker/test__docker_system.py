import pytest
from click.testing import CliRunner
from docker_test_utils import *

from commands.docker import cli as docker
from commands.docker import try_docker_system


import logging

import json

@pytest.mark.docker
@pytest.mark.integration
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestDockerSystem:

    def test_minimal(self, monkeypatch):
        runner = CliRunner()

        result = try_docker_system()

        if not result['success']:
            if 'connection refused' in result['logs'].lower():
                logging.error("Docker installed, but connection to dockerd failed.")
            else:
                logging.error(result['logs'])

        assert result['success']
