import filecmp

import pytest
from click.testing import CliRunner

from commands.report import cli as report
from tests.helpers.test_utils import *
from neoload_cli_lib import tools


@pytest.mark.report
class TestTrendsTemplates:

    def test_builtin_transactions(self, monkeypatch):
        actual_file_path = 'tests/resources/report/actual_template_trends.html'
        expected_file_path = 'tests/resources/report/expected_template_trends.html'
        if monkeypatch:
            monkeypatch.setattr(tools, 'compute_version', lambda: '1.1.8')
        runner = CliRunner()
        result_report = runner.invoke(report, ['--json-in', 'tests/resources/report/expected_trends.json', '--template',
                                               'neoload/resources/jinja/sample-trends-report.html.j2', '--out-file',
                                               actual_file_path])
        assert_success(result_report)
        set_line_endings_to_lf(actual_file_path)
        assert filecmp.cmp(actual_file_path,
                           expected_file_path) is True, f"Json output for the report (file {actual_file_path}) is not the one expected (file {expected_file_path})"
