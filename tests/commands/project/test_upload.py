import pytest
from click.testing import CliRunner
from commands.project import cli as project
from commands.status import cli as status
from helpers.test_utils import *


@pytest.mark.project
class TestUpload:

    @pytest.mark.datafiles('tests/neoload_projects/example_1.zip')
    @pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
    def test_upload(self, monkeypatch, datafiles, valid_data):
        zip_path = datafiles.listdir()[0]
        runner = CliRunner()
        mock_api_post_binary(monkeypatch, 'v2/tests/%s/project' % valid_data.test_settings_id, 200,
                             '{"projectId":"5e5fc0102cc4f82e5d9e18d4", "projectName":"NeoLoad-CLI-example-2_0",'
                             '"asCodeFiles": [{"path": "default.yaml", "includes": ["paths/geosearch_get.yaml"]}],'
                             '"scenarios":[{"scenarioName": "sanityScenario","scenarioDuration": 10,"scenarioVUs": 2,"scenarioSource": "default.yaml"}]}')
        result_upload = runner.invoke(project, ['--path', zip_path, 'upload', valid_data.test_settings_id])
        assert_success(result_upload)
        json_upload = json.loads(result_upload.output)
        assert json_upload['projectName'] == 'NeoLoad-CLI-example-2_0'
        assert str(json_upload['asCodeFiles'][0]['path']).endswith('default.yaml')
        assert json_upload['asCodeFiles'][0]['includes'][0] == 'paths/geosearch_get.yaml'
        assert json_upload['scenarios'][0]['scenarioName'] == 'sanityScenario'
        assert json_upload['scenarios'][0]['scenarioDuration'] == 10
        assert json_upload['scenarios'][0]['scenarioVUs'] == 2
        assert str(json_upload['scenarios'][0]['scenarioSource']).endswith('default.yaml')

        result_status = runner.invoke(status)
        assert_success(result_status)
        assert 'settings id: %s' % valid_data.test_settings_id in result_status.output
