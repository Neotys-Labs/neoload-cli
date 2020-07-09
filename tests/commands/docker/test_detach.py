import pytest
from click.testing import CliRunner
from docker_test_utils import *

from commands.docker import cli as docker

@pytest.mark.docker
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestDetach:
    def test_minimal(self, monkeypatch):
        runner = CliRunner()

        def validate(context, result):
            assert_success(result)
            print(result.output)

            assert ('No containers or networks' in result.output or
                    'All containers and networks with' in result.output or
                    '0 artifacts' in result.output
            )

        setup_lifecycle(runner,
            between_create_delete=lambda context: attach_detach_lifecycle(context,
                after_detach=validate
            )
        )

    def test_all_detach(self, monkeypatch):
        runner = CliRunner()

        detach_result = runner.invoke(docker, ['--all', 'detach'])
        assert_success(detach_result)
