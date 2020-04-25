import pytest
from click.testing import CliRunner
from docker_test_utils import *

from commands.docker import cli as docker
from commands.docker import key_meta_prior_docker
from commands.status import cli as status

@pytest.mark.docker
@pytest.mark.integration
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestPrepare:
    def test_minimal(self, monkeypatch):
        runner = CliRunner()

        setup_lifecycle(runner,
            between_create_delete=lambda context: run_prepare_command(runner, context)
        )

# this is also used by 'forget' tests
def run_prepare_command(runner, context):
    # prepare takes from test-settings (created and configured in lifecycle)
    prepare_result = runner.invoke(docker, ['prepare'])
    assert_success(prepare_result)

    # the sign of a successful prepare is that there is meta that will be used by 'run'
    status_result = runner.invoke(status)
    assert_success(status_result)
    assert key_meta_prior_docker+': {' in status_result.output
