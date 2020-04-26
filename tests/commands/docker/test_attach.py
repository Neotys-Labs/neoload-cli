import pytest
from click.testing import CliRunner
from docker_test_utils import *

@pytest.mark.docker
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestAttach:
    def test_minimal(self, monkeypatch):
        runner = CliRunner()

        def validate(context, result):
            assert_success(result)
            assert 'All containers are attached' in result.output

        setup_lifecycle(runner,
            between_create_delete=lambda context: attach_detach_lifecycle(context,
                after_attach=validate
            )
        )
