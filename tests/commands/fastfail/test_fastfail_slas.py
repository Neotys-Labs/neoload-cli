import pytest
import os
from click.testing import CliRunner
from commands.login import cli as login
from commands.status import cli as status
from commands.test_results import cli as results
from commands.fastfail import cli as fastfail
from helpers.test_utils import *

@pytest.mark.fastfail
@pytest.mark.slow
@pytest.mark.makelivecalls
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestFastfailSlas:
    def test_fastfail_on_completed_test_raw(self):
        runner = CliRunner()
        result = runner.invoke(results, ['use','raw'])
        assert_success(result)
        result = runner.invoke(fastfail, ['--max-failure','25','slas'])
        assert result.exit_code==1
        assert 'fastfail ended:' in result.output
