import pytest
import os
from click.testing import CliRunner
from commands.login import cli as login
from commands.status import cli as status
from commands.test_results import cli as results
from commands.fastfail import cli as fastfail
from tests.helpers.test_utils import *

@pytest.mark.fastfail
@pytest.mark.slow
@pytest.mark.makelivecalls
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestFastfailSlas:
    def test_fastfail_invalid_no_parameters(self):
        runner = CliRunner()
        result = runner.invoke(fastfail)
        assert result.exit_code==2
        assert 'Missing argument' in result.output

    def test_fastfail_invalid_max_low(self):
        runner = CliRunner()
        result = runner.invoke(fastfail, ['--max-failure=-1','slas'])
        assert result.exit_code==2
        assert 'percentage tolerance must be between 0 and 100' in result.output

    def test_fastfail_invalid_max_high(self):
        runner = CliRunner()
        result = runner.invoke(fastfail, ['--max-failure=125','slas'])
        assert result.exit_code==2
        assert 'percentage tolerance must be between 0 and 100' in result.output

    def test_fastfail_invalid_bad_name(self):
        runner = CliRunner()
        invalid_name = 'this_is_an_invalid_test_result_name'
        result = runner.invoke(fastfail, ['--max-failure=25','slas',invalid_name])
        assert result.exit_code==1
        assert "No id associated to the name '{}'".format(invalid_name) in result.output

    def test_fastfail_on_completed_test_raw(self):
        runner = CliRunner()
        result = runner.invoke(results, ['use','raw'])
        assert_success(result)
        result = runner.invoke(fastfail, ['--max-failure','25','slas'])
        assert result.exit_code==1
        assert 'fastfail ended:' in result.output
