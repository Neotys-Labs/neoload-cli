import time
from urllib.parse import quote

import pytest
from click.testing import CliRunner
from commands.login import cli as login
from commands.logout import cli as logout
from commands.status import cli as status
from commands.test_settings import cli as settings
from commands.project import cli as project
from commands.validate import cli as validate
from commands.run import cli as run
from commands.stop import cli as stop

from helpers.test_utils import *


@pytest.mark.acceptance
class TestReadme:
    pytest.test_name = generate_test_settings_name()
    pytest.result_name = generate_test_result_name()
    pytest.test_id = '56d23aee-6e4d-428e-8164-543066718e9b'
    pytest.result_id = None

    @pytest.mark.datafiles('tests/neoload_projects/example_1')
    @pytest.mark.usefixtures('neoload_login')
    def test_tl_dr(self, monkeypatch, datafiles):
        folder_path = datafiles
        runner = CliRunner()
        mock_api_post(monkeypatch, 'v2/tests',
                      '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":"",'
                      '"scenarioName":"sanityScenario", "controllerZoneId":"a-zone", '
                      '"lgZoneIds":{"a-zone":5}, "testResultNamingPattern":"#${runID}"}' % pytest.test_name)
        result_create = runner.invoke(settings, ['--zone', 'a-zone', '--lgs', 'a-zone:5', '--scenario',
                                                 'sanityScenario', 'create', pytest.test_name])
        assert_success(result_create)
        json_create = json.loads(result_create.output)
        pytest.test_id = json_create['id']
        assert pytest.test_id is not None
        assert json_create['name'] == pytest.test_name
        assert json_create['controllerZoneId'] == 'a-zone'
        assert json_create['lgZoneIds']['a-zone'] == 5
        assert json_create['testResultNamingPattern'] == '#${runID}'

        mock_api_post_binary(monkeypatch, 'v2/tests/%s/project' % pytest.test_id, 200,
                             '{"projectId":"5e5fc0102cc4f82e5d9e18d4", "projectName":"NeoLoad-CLI-example-2_0",'
                             '"asCodeFiles": [{"path": "default.yaml", "includes": ["paths/geosearch_get.yaml"]}],'
                             '"scenarios":[{"scenarioName": "sanityScenario","scenarioDuration": 60,"scenarioVUs": 5,"scenarioSource": "default.yaml"}]}')
        result_upload = runner.invoke(project, ['--path', folder_path, 'upload'])
        assert_success(result_upload)
        json_upload = json.loads(result_upload.output)
        assert json_upload['projectName'] == 'NeoLoad-CLI-example-2_0'
        assert str(json_upload['asCodeFiles'][0]['path']).endswith('default.yaml')
        assert json_upload['asCodeFiles'][0]['includes'][0] == 'paths/geosearch_get.yaml'
        assert json_upload['scenarios'][0]['scenarioName'] == 'sanityScenario'
        assert json_upload['scenarios'][0]['scenarioDuration'] == 60
        assert json_upload['scenarios'][0]['scenarioVUs'] == 5
        assert str(json_upload['scenarios'][0]['scenarioSource']).endswith('default.yaml')

    def test_status(self, monkeypatch):
        runner = CliRunner()
        result_logout = runner.invoke(logout)
        assert_success(result_logout)
        assert 'logout successfully' in result_logout.output

        result_status1 = runner.invoke(status)
        assert_success(result_status1)
        assert 'No settings is stored. Please use "neoload login" to start.' in result_status1.output

        mock_api_get_raw(monkeypatch, 'v3/information', 200,
                         '{"front_url":"https://neoload.saas.neotys.com/", "filestorage_url":"https://neoload-files.saas.neotys.com", "version":"SaaS"}')
        result_login = runner.invoke(login, ['123456789fe70bf4a991ae6d8af62e21c4a00203abcdef'])
        assert_success(result_login)
        assert '' == result_login.output

        result_status2 = runner.invoke(status)
        assert_success(result_status2)
        assert 'You are logged on https://neoload-api.saas.neotys.com/ with token *******************************************def' in result_status2.output
        assert 'frontend url: https://neoload.saas.neotys.com' in result_status2.output
        assert 'file storage url: https://neoload-files.saas.neotys.com' in result_status2.output
        assert 'version: SaaS' in result_status2.output

    @pytest.mark.usefixtures('neoload_login')
    def test_use(self, monkeypatch, invalid_data):
        runner = CliRunner()
        if pytest.test_id is None:
            pytest.test_id = '70ed01da-f291-4e29-b75c-1f7977edf252'
        result_use = runner.invoke(settings, ['use', invalid_data.uuid])
        assert_success(result_use)
        result_status1 = runner.invoke(status)
        assert_success(result_status1)
        assert 'settings id: %s' % invalid_data.uuid in result_status1.output

        mock_api_get_with_pagination(monkeypatch, 'v2/tests', '[{"id":"%s", "name":"%s"}]' % (pytest.test_id, pytest.test_name))
        result_use2 = runner.invoke(settings, ['use', pytest.test_name])
        assert_success(result_use2)
        result_status2 = runner.invoke(status)
        assert_success(result_status2)
        assert 'settings id: %s' % pytest.test_id in result_status2.output

    @pytest.mark.datafiles('tests/neoload_projects/example_1/')
    def test_upload(self, monkeypatch, datafiles):
        folder_path = datafiles
        runner = CliRunner()
        if pytest.test_id is None:
            pytest.test_id = '70ed01da-f291-4e29-b75c-1f7977edf252'
        mock_api_post_binary(monkeypatch, 'v2/tests/%s/project' % pytest.test_id, 200,
                             '{"projectId":"5e5fc0102cc4f82e5d9e18d4", "projectName":"NeoLoad-CLI-example-2_0",'
                             '"asCodeFiles": [{"path": "default.yaml", "includes": ["paths/geosearch_get.yaml"]}],'
                             '"scenarios":[{"scenarioName": "sanityScenario","scenarioDuration": 60,"scenarioVUs": 5,"scenarioSource": "default.yaml"}]}')
        result_upload = runner.invoke(project, ['--path', folder_path, 'upload'])
        assert_success(result_upload)
        json_upload = json.loads(result_upload.output)
        assert json_upload['projectName'] == 'NeoLoad-CLI-example-2_0'
        assert str(json_upload['asCodeFiles'][0]['path']).endswith('default.yaml')
        assert json_upload['asCodeFiles'][0]['includes'][0] == 'paths/geosearch_get.yaml'
        assert json_upload['scenarios'][0]['scenarioName'] == 'sanityScenario'
        assert json_upload['scenarios'][0]['scenarioDuration'] == 60
        assert json_upload['scenarios'][0]['scenarioVUs'] == 5
        assert str(json_upload['scenarios'][0]['scenarioSource']).endswith('default.yaml')

        result_status = runner.invoke(status)
        assert_success(result_status)
        assert 'settings id: %s' % pytest.test_id in result_status.output

    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    def test_validate(self, datafiles):
        file_path = datafiles.listdir()[0]
        runner = CliRunner()
        result = runner.invoke(validate, [str(file_path), '--refresh'])
        assert_success(result)
        assert 'Yaml file is valid' in str(result.output)

    def test_run_with_detach(self, monkeypatch):
        runner = CliRunner()
        if pytest.test_id is None:
            pytest.test_id = '70ed01da-f291-4e29-b75c-1f7977edf252'

        # Prepare the test
        mock_api_patch(monkeypatch, 'v2/tests/%s' % pytest.test_id,
                       '{"id":"some id", "name":"some name", "controllerZoneId":"cuPd2", "lgZoneIds":{"cuPd2":1}}')
        result_patch = runner.invoke(settings, ['patch', '--zone', 'cuPd2', pytest.test_id])
        assert_success(result_patch)

        # Run the test
        mock_api_get(monkeypatch, 'v2/tests/%s' % pytest.test_id,
                     '{"id":"%s", "name":"test-name", "nextRunId":1}' % pytest.test_id)
        mock_api_post(monkeypatch, 'v2/tests/%s/start?testResultName=%s' % (pytest.test_id, quote(pytest.result_name)),
                      '{"resultId": "9f54dacd-e793-4553-9f16-d4cc7adba545"}')
        result_run = runner.invoke(run, ['-d', '--name', pytest.result_name])
        assert_success(result_run)
        json_run = json.loads(result_run.output)
        pytest.result_id = json_run['resultId']
        result_status = runner.invoke(status)
        assert_success(result_status)
        assert 'result id: %s' % json_run['resultId'] in result_status.output

    def test_stop(self, monkeypatch):
        runner = CliRunner()
        if pytest.result_id is None:
            pytest.result_id = '9f54dacd-e793-4553-9f16-d4cc7adba545'
        mock_api_post(monkeypatch, 'v2/test-results/%s/stop' % pytest.result_id,
                      '{"testResultId": "%s"}' % pytest.result_id)

        if monkeypatch is None:
            # Wait until test is running before try to stop it
            state = "INIT"
            while state != "RUNNING" and state != "TERMINATED":
                time.sleep(10)
                state = rest_crud.get('v2/test-results/' + pytest.result_id)['status']

        result_stop = runner.invoke(stop)
        assert_success(result_stop)
        assert result_stop.output == ''

    # This test is disabled when mocks are active
    def test_run_with_wait(self, monkeypatch):
        if monkeypatch is not None:
            # TODO To handle a success test with mocks, we need to be able to mock again GET with the
            # TODO endpoint v2/test-results to return data (that could evolve until a "terminate" status...)
            return
        runner = CliRunner()
        random_result_name = generate_test_result_name()
        if pytest.test_id is None:
            pytest.test_id = '70ed01da-f291-4e29-b75c-1f7977edf252'
        mock_api_get(monkeypatch, 'v2/tests/%s' % pytest.test_id,
                     '{"id":"%s", "name":"test-name", "nextRunId":1}' % pytest.test_id)
        mock_api_post(monkeypatch, 'v2/tests/%s/start?testResultName=%s' % (pytest.test_id, quote(random_result_name)),
                      '{"resultId": "9f54dacd-e793-4553-9f16-d4cc7adba545"}')
        result_run = runner.invoke(run, ['--name', random_result_name,
                                         '--as-code', 'default.yaml,slas/uat.yaml', '--description',
                                         'A custom test description containing hashtags like #latest or #issueNum'
                                         ])
        assert result_run.exit_code == 2
        assert 'Status: INIT' in result_run.output
        assert 'Status: RUNNING' in result_run.output
        assert 'Status: TERMINATED' in result_run.output
        assert 'Test completed with 7 SLAs failures' in result_run.output
