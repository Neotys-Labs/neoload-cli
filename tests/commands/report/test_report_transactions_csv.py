import pytest
import os
from click.testing import CliRunner
from commands.login import cli as login
from commands.test_results import cli as results
from commands.report import cli as report
from helpers.test_utils import *

@pytest.mark.report
@pytest.mark.slow
@pytest.mark.makelivecalls
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestResultLs:
    def test_builtin_transactions_csv(self, monkeypatch):
        runner = CliRunner()
        #result = runner.invoke(login, ['--workspace','Team A',os.getenv("NLW_TOKEN")])
        #assert_success(result)
        result = runner.invoke(results, ['use','raw'])
        assert_success(result)
        result = runner.invoke(report, ['--template','builtin:transactions-csv','--filter','timespan=1%-2m','cur'])
        assert_success(result)
        assert 'User Path;' in result.output
        print(result.output)
