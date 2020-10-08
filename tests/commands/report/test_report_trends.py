import pytest
import os
from click.testing import CliRunner
from commands.login import cli as login
from commands.test_results import cli as results
from commands.report import cli as report
from commands.report import is_guid
from helpers.test_utils import *
import json
import tempfile

@pytest.mark.report
@pytest.mark.slow
@pytest.mark.makelivecalls
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestReportTrends:
    def test_trend_export_and_template_out(self):
        runner = CliRunner()

        # get a result as the baseline
        result = runner.invoke(results, [
            #'--filter','project=CPVWeatherCrisis;sort=-startDate',
            'ls'
        ])
        assert_success(result)

        centers = json.loads(result.output)
        centers = list(filter(lambda x: x['project']=='CPVWeatherCrisis' and x['scenario']=='Post Nominal Test', centers))
        assert len(centers) > 1
        __id = centers[0]['id']
        assert is_guid(__id)

        with tempfile.NamedTemporaryFile(suffix='.json', prefix='neoload-cli.test.report.trends') as tf:
            json_file = tf.name

            # export trend data
            result = runner.invoke(report, [
                '--type','trends',
                '--filter','results=-1;elements=Submit|Map',
                '--out-file',json_file,
                __id
            ])
            assert_success(result)

            # export trend data
            result = runner.invoke(report, [
                '--type','trends',
                '--json-in',json_file,
                '--template','tests/resources/jinja/sample-trends-report.html.j2',
                __id
            ])
            assert '<html>' in result.output
