import pytest
from click.testing import CliRunner
from docker_test_utils import *

from commands.docker import cli as docker
from commands.docker import key_meta_prior_docker
from commands.status import cli as status
from test_prepare import run_prepare_command

@pytest.mark.docker
@pytest.mark.integration
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestForget:
    def test_minimal(self, monkeypatch):
        runner = CliRunner()

        def run_prepare_and_forget_commands(runner, context):
            run_prepare_command(runner, context)
            run_forget_command(runner, context)

        setup_lifecycle(runner,
            between_create_delete=lambda context: run_prepare_and_forget_commands(runner, context)
        )

    def test_with_prior_attach_and_run_id(self, monkeypatch):
        runner = CliRunner()

        def run_prepare_attach_forget_commands(runner, context):
            run_prepare_command(runner, context)
            attach_result = runner.invoke(docker, ['attach'])
            assert_success(attach_result)
            run_forget_command(runner, context)

        setup_lifecycle(runner,
            between_create_delete=lambda context: run_prepare_attach_forget_commands(runner, context)
        )


def run_forget_command(runner,context):
    # forget deletes the meta used by run, docker.key_meta_prior_docker
    forget_result = runner.invoke(docker, ['forget'])
    assert_success(forget_result)

    # the sign of a successful prepare is that there is no meta that will be used by 'run'
    status_result = runner.invoke(status)
    assert_success(status_result)
    assert key_meta_prior_docker+': {' not in status_result.output
