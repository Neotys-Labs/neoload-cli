import time
from urllib.parse import quote

import pytest
from click.testing import CliRunner
from commands.login import cli as login
from commands.logout import cli as logout
from commands.status import cli as status
from commands.test_settings import cli as settings
from commands.workspaces import cli as workspaces
from commands.test_results import cli as results

from tests.helpers.test_utils import *


@pytest.mark.makelivecalls
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestStatusWithNames:
    def test_status_with_name_resolution(self, monkeypatch):
        runner = CliRunner()

        results_use = runner.invoke(results, ['use','raw'])
        assert_success(results_use)

        runner.invoke(settings, ['use'])
        settings_use = runner.invoke(settings, ['use','e717b07c-16d9-4204-bb1e-0ad3ef2cfabd'])
        assert_success(settings_use)

        result_status2 = runner.invoke(status)
        assert_success(result_status2)

        assert 'workspace id: 5faa59f2c7851770df1de989 (CLI)' in result_status2.output
        assert 'result id: 7419f98b-7f39-46da-a02f-f378f7aaec97 (raw)' in result_status2.output
        assert 'settings id: e717b07c-16d9-4204-bb1e-0ad3ef2cfabd (For Unit Tests Report Command (DO NOT REMOVE))' in result_status2.output
