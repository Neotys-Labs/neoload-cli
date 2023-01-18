import pytest
import os
from click.testing import CliRunner
from commands.login import cli as login
from commands.test_results import cli as results
from commands.report import cli as report
from tests.helpers.test_utils import *
import tempfile

@pytest.mark.report
@pytest.mark.slow
@pytest.mark.makelivecalls
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestReportTransactions:
    def test_builtin_transactions_csv_raw(self):
        runner = CliRunner()
        result = runner.invoke(results, ['use','raw'])
        assert_success(result)
        result = runner.invoke(report, ['--template','builtin:transactions-csv','--filter','timespan=1%-2m','cur'])
        assert_success(result)
        assert 'User Path;' in result.output

    def test_builtin_transactions_csv_not_raw(self):
        runner = CliRunner()
        result = runner.invoke(results, ['use','not_raw'])
        assert_success(result)
        result = runner.invoke(report, ['--template','builtin:transactions-csv','--filter','timespan=1%-2m','cur'])
        assert_success(result)
        assert 'User Path;' in result.output

    def test_custom_template(self):
        runner = CliRunner()
        result = runner.invoke(results, ['use','raw'])
        assert_success(result)
        with tempfile.NamedTemporaryFile(suffix='.json', prefix='neoload-cli.test.report.transactions') as tf:
            json_file = tf.name
            result = runner.invoke(report, ['--template','builtin:transactions','--out-file',json_file,'cur'])
            assert_success(result)
            result = runner.invoke(report, ['--template','neoload/resources/jinja/custom_transactions_export.j2','--json-in',json_file,'cur'])
            assert_success(result)
            assert 'User Path,' in result.output

    def test_no_template(self):
        runner = CliRunner()
        result = runner.invoke(results, ['use','raw'])
        assert_success(result)
        with tempfile.NamedTemporaryFile(suffix='.json', prefix='neoload-cli.test.report.transactions') as tf:
            json_file = tf.name
            result = runner.invoke(report, ['--out-file',json_file,'cur'])
            assert_success(result)
            # asert that file content is JSON and contains at least "summary":
