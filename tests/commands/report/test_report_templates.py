import filecmp

import pytest
from click.testing import CliRunner

from commands.report import cli as report
from tests.helpers.test_utils import *
from neoload_cli_lib import tools


@pytest.mark.report
class TestReportTemplates:

    def test_builtin_transactions(self, monkeypatch):
        actual_file_path = 'tests/resources/report/actual_template_transactions.json'
        expected_file_path = 'tests/resources/report/expected_template_transactions.json'
        if monkeypatch:
            monkeypatch.setattr(tools, 'compute_version', lambda: '1.1.8')
        runner = CliRunner()
        result_report = runner.invoke(report, ['--json-in', 'tests/resources/report/expected_report.json', '--template',
                                               'builtin:transactions', '--out-file', actual_file_path])
        assert_success(result_report)
        # Indent json output before comparison, so the expected json file is easier to compare by a human (git diff)
        with open(actual_file_path, 'r+', newline='\n') as actual:
            file_content = json.load(actual)
            actual.write(json.dumps(file_content, indent=2))
        assert filecmp.cmp(actual_file_path,
                           expected_file_path) is True, f"Json output for the report (file {actual_file_path}) is not the one expected (file {expected_file_path})"

    def test_builtin_transactions_csv(self):
        actual_file_path = 'tests/resources/report/actual_template_transactions_csv.csv'
        expected_file_path = 'tests/resources/report/expected_template_transactions_csv.csv'
        runner = CliRunner()
        result_report = runner.invoke(report, ['--json-in', 'tests/resources/report/expected_report.json', '--template',
                                               'builtin:transactions-csv', '--out-file', actual_file_path])
        assert_success(result_report)
        set_line_endings_to_lf(actual_file_path)
        assert filecmp.cmp(actual_file_path,
                           expected_file_path) is True, f"Template output (file {actual_file_path}) is not the one expected (file {expected_file_path})"

    def test_custom_report_html(self):
        actual_file_path = 'tests/resources/report/actual_custom_report.html'
        expected_file_path = 'tests/resources/report/expected_custom_report.html'
        runner = CliRunner()
        result_report = runner.invoke(report, ['--json-in', 'tests/resources/report/expected_report.json', '--template',
                                               'tests/resources/jinja/sample-custom-report.html.j2', '--out-file',
                                               actual_file_path])
        assert_success(result_report)
        set_line_endings_to_lf(actual_file_path)
        assert filecmp.cmp(actual_file_path,
                           expected_file_path) is True, f"Template output (file {actual_file_path}) is not the one expected (file {expected_file_path})"

    def test_custom_report_html_filtered(self):
        actual_file_path = 'tests/resources/report/actual_custom_report_filtered.html'
        expected_file_path = 'tests/resources/report/expected_custom_report_filtered.html'
        runner = CliRunner()
        result_report = runner.invoke(report, ['--json-in', 'tests/resources/report/expected_report_filtered.json',
                                               '--template', 'tests/resources/jinja/sample-custom-report.html.j2',
                                               '--out-file', actual_file_path])
        assert_success(result_report)
        set_line_endings_to_lf(actual_file_path)
        assert filecmp.cmp(actual_file_path,
                           expected_file_path) is True, f"Template output (file {actual_file_path}) is not the one expected (file {expected_file_path})"

    def test_custom_transactions_csv(self):
        actual_file_path = 'tests/resources/report/actual_custom_transactions.csv'
        expected_file_path = 'tests/resources/report/expected_custom_transactions.csv'
        runner = CliRunner()
        result_report = runner.invoke(report, ['--json-in', 'tests/resources/report/expected_report.json', '--template',
                                               'tests/resources/jinja/custom_transactions_export.j2', '--out-file',
                                               actual_file_path])
        assert_success(result_report)
        set_line_endings_to_lf(actual_file_path)
        assert filecmp.cmp(actual_file_path,
                           expected_file_path) is True, f"Template output (file {actual_file_path}) is not the one expected (file {expected_file_path})"
