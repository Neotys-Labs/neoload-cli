import pytest
from click.testing import CliRunner
from tests.helpers.test_utils import *

from commands.wait import cli as wait
from neoload_cli_lib import running_tools


@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestWait:
    def test_wait(self, monkeypatch):
        runner = CliRunner()
        monkeypatch.setattr(running_tools, 'wait',
                            lambda results_id, exit_code_sla, data_lock: self.__assert_values(results_id, exit_code_sla,
                                                                                              data_lock, True))
        result_wait = runner.invoke(wait, ['b78c29f7-2d7b-4524-b950-1b011a704e06'])
        assert_success(result_wait)

    def test_wait_return0(self, monkeypatch):
        runner = CliRunner()
        monkeypatch.setattr(running_tools, 'wait',
                            lambda results_id, exit_code_sla, data_lock: self.__assert_values(results_id, exit_code_sla,
                                                                                              data_lock, False))
        result_wait = runner.invoke(wait, ['--return-0', 'b78c29f7-2d7b-4524-b950-1b011a704e06'])
        assert_success(result_wait)

    def __assert_values(self, results_id, exit_code_sla, data_lock, expected_exit_code):
        assert results_id == 'b78c29f7-2d7b-4524-b950-1b011a704e06'
        assert exit_code_sla is expected_exit_code
        assert data_lock == {}
