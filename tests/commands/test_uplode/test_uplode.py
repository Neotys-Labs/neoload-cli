import pytest
from click.testing import CliRunner
from commands.project import cli as project
from tests.helpers.test_utils import *
from neoload_cli_lib import neoLoad_project


@pytest.mark.project
class TestPasswordInNLP:

    @pytest.mark.datafiles('tests/neoload_projects/example_1.zip')
    @pytest.mark.usefixtures("neoload_login")
    def test_password_in_nlp(self, monkeypatch, datafiles, valid_data):
        zip_path = datafiles / 'example_1.zip'
        runner = CliRunner()

        assert zip_path.exists()
        assert zip_path.suffix == '.zip'

        mock_api_post_binary(monkeypatch, 'v2/tests/%s/project' % valid_data.test_settings_id, 200,
                             '{"projectId":"5e5fc0102cc4f82e5d9e18d4", "projectName":"NeoLoad-CLI-example-2_0",'
                             '"asCodeFiles": [{"path": "default.yaml", "includes": ["paths/geosearch_get.yaml"]}],'
                             '"scenarios":[{"scenarioName": "sanityScenario","scenarioDuration": 10,"scenarioVUs": 2,"scenarioSource": "default.yaml"}]}')

        result_upload = runner.invoke(project, ['--path', str(zip_path), 'upload', valid_data.test_settings_id])

        assert_success(result_upload)

        assert "Your project has a password, please go here to enter your password:" in result_upload.output

    @pytest.mark.datafiles('tests/neoload_projects/example_2.zip')
    @pytest.mark.usefixtures("neoload_login")
    def test_no_password_in_nlp(self, monkeypatch, datafiles, valid_data):
        zip_path = datafiles / 'example_2.zip'
        runner = CliRunner()

        assert zip_path.exists()
        assert zip_path.suffix == '.zip'

        mock_api_post_binary(monkeypatch, 'v2/tests/%s/project' % valid_data.test_settings_id, 200,
                             '{"projectId":"5e5fc0102cc4f82e5d9e18d4", "projectName":"NeoLoad-CLI-example-2_0",'
                             '"asCodeFiles": [{"path": "default.yaml", "includes": ["paths/geosearch_get.yaml"]}],'
                             '"scenarios":[{"scenarioName": "sanityScenario","scenarioDuration": 10,"scenarioVUs": 2,"scenarioSource": "default.yaml"}]}')

        result_upload = runner.invoke(project, ['--path', str(zip_path), 'upload', valid_data.test_settings_id])

        assert_success(result_upload)

        assert "Your project has a password, please go here to enter your password:" not in result_upload.output
