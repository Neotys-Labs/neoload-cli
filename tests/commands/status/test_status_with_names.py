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

        settings_use = runner.invoke(settings, ['use','180938f4-5749-493c-a341-cbe48d9f1a57'])
        assert_success(settings_use)

        result_status2 = runner.invoke(status)
        assert_success(result_status2)

        assert 'workspace id: 5fcaeff6430f780001e3fb3e (CLI)' in result_status2.output
        assert 'result id: 44f1a611-bad3-451f-a7d5-9534cf62ee26 (raw)' in result_status2.output
        assert 'settings id: 180938f4-5749-493c-a341-cbe48d9f1a57 (For Unit Tests Report Command (Do not remove))' in result_status2.output
