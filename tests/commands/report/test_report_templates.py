import filecmp

import pytest
from click.testing import CliRunner

from commands.report import cli as report
from helpers.test_utils import *
from neoload_cli_lib import tools


@pytest.mark.report
class TestReportTemplates:

    def test_builtin_transactions(self, monkeypatch):
        if monkeypatch:
            monkeypatch.setattr(tools, 'compute_version', lambda: '1.1.8')
        runner = CliRunner()
        result_report = runner.invoke(report, ['--json-in', 'tests/resources/report/expected_report.json', '--template',
                                               'builtin:transactions', '--out-file',
                                               'tests/resources/report/actual_template_transactions.json'])
        assert_success(result_report)
        assert filecmp.cmp('tests/resources/report/actual_template_transactions.json', 'tests/resources/report/expected_template_transactions.json') is True, "Json output for the report (file tests/resources/report/actual_template_transactions.json) is not the one expected (file tests/resources/report/expected_template_transactions.json)"

    def test_builtin_transactions_csv(self):
        runner = CliRunner()
        result_report = runner.invoke(report, ['--json-in', 'tests/resources/report/expected_report.json', '--template',
                                               'builtin:transactions-csv', '--out-file',
                                               'tests/resources/report/actual_template_transactions_csv.csv'])
        assert_success(result_report)
        assert filecmp.cmp('tests/resources/report/actual_template_transactions_csv.csv', 'tests/resources/report/expected_template_transactions_csv.csv') is True, "Template output (file tests/resources/report/actual_template_transactions_csv.csv) is not the one expected (file tests/resources/report/expected_template_transactions_csv.csv)"

    def test_custom_report_html(self):
        runner = CliRunner()
        result_report = runner.invoke(report, ['--json-in', 'tests/resources/report/expected_report.json', '--template',
                                               'tests/resources/jinja/sample-custom-report.html.j2', '--out-file',
                                               'tests/resources/report/actual_custom_report.html'])
        assert_success(result_report)
        assert filecmp.cmp('tests/resources/report/actual_custom_report.html', 'tests/resources/report/expected_custom_report.html') is True, "Template output (file tests/resources/report/actual_custom_report.html) is not the one expected (file tests/resources/report/expected_custom_report.html)"

    def test_custom_transactions_csv(self):
        runner = CliRunner()
        result_report = runner.invoke(report, ['--json-in', 'tests/resources/report/expected_report.json', '--template',
                                               'tests/resources/jinja/custom_transactions_export.j2', '--out-file',
                                               'tests/resources/report/actual_custom_transactions.csv'])
        assert_success(result_report)
        assert filecmp.cmp('tests/resources/report/actual_custom_transactions.csv', 'tests/resources/report/expected_custom_transactions.csv') is True, "Template output (file tests/resources/report/actual_custom_transactions.csv) is not the one expected (file tests/resources/report/expected_custom_transactions.csv)"
