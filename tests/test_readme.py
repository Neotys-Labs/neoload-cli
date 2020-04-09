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
    __test_name = 'NewTest1'
    __test_id = None
    __result_id = None

    @pytest.mark.datafiles('tests/neoload_projects/example_1')
    @pytest.mark.usefixtures('neoload_login')
    def tl_dr(self, monkeypatch):
        runner = CliRunner()
        mock_api_post(monkeypatch, 'v2/tests',
                      '{"id":"70ed01da-f291-4e29-b75c-1f7977edf252", "name":"%s", "description":"",'
                      '"scenarioName":"sanityScenario", "controllerZoneId":"a-zone", '
                      '"lgZoneIds":{"a-zone":5}, "testResultNamingPattern":"#${runId}"}' % self.__test_name)
        result_create = runner.invoke(settings, ['--zone', 'a-zone', '--lgs', 'a-zone:5', '--scenario',
                                                 'sanityScenario', 'create', self.__test_name])
        assert_success(result_create)
        json_create = json.loads(result_create.output)
        self.__test_id = json_create['id']
        assert json_create['name'] == self.__test_name
        assert json_create['controllerZoneId'] == 'a-zone'
        assert json_create['lgZoneIds']['a-zone'] == 5
        assert json_create['testResultNamingPattern'] == '#${runId}'

        mock_api_post_binary(monkeypatch, 'v2/tests/%s/project' % json_create['id'],
                             '{"id":"5e5fc0102cc4f82e5d9e18d4", "name":"Project", "description":"",'
                             '"scenarioName":"sanityScenario", "controllerZoneId":"a-zone", '
                             '"lgZoneIds":{"a-zone":5}, "testResultNamingPattern":"#${runId}"}')
        result_upload = runner.invoke(project, ['--path', 'tests/neoload_projects/example_1', 'upload'])
        assert_success(result_upload)
        json_upload = json.loads(result_upload.output)
        assert json_upload['projectName'] == 'NeoLoad-as-code-examples-2_0'
        assert json_upload['projectVersion'] == 'NeoLoad-CLI-example-2_0'
        assert json_upload['asCodeFiles'][0]['path'] == 'paths/geosearch_get.yaml'
        assert json_upload['scenarios'][0]['scenarioName'] == 'sanityScenario'

    def test_status(self, monkeypatch):
        runner = CliRunner()
        result_logout = runner.invoke(logout)
        assert_success(result_logout)
        assert 'logout successfully' in result_logout.output

        result_status1 = runner.invoke(status)
        assert_success(result_status1)
        assert 'No settings is stored. Please use "neoload login" to start.' in result_status1.output

        result_login = runner.invoke(login, ['123456789fe70bf4a991ae6d8af62e21c4a00203abcdef'])
        assert_success(result_login)
        assert '' == result_login.output

        result_status2 = runner.invoke(status)
        assert_success(result_status2)
        assert 'You are logged on https://neoload-api.saas.neotys.com/ with token *******************************************def' in result_status2.output

    @pytest.mark.usefixtures('neoload_login')
    def test_use(self, monkeypatch, invalid_data):
        runner = CliRunner()
        if self.__test_id is None:
            self.__test_id = '70ed01da-f291-4e29-b75c-1f7977edf252'
        result_use = runner.invoke(settings, ['use', invalid_data.uuid])
        assert_success(result_use)
        result_status1 = runner.invoke(status)
        assert_success(result_status1)
        assert 'settings id: %s' % invalid_data.uuid in result_status1.output

        mock_api_get(monkeypatch, 'v2/tests', '[{"id":"%s", "name":"%s"}]' % (self.__test_id, self.__test_name))
        result_use2 = runner.invoke(settings, ['use', self.__test_name])
        assert_success(result_use2)
        result_status2 = runner.invoke(status)
        assert_success(result_status2)
        assert 'settings id: %s' % self.__test_id in result_status2.output

    @pytest.mark.datafiles('tests/neoload_projects/example_1/')
    def test_upload(self, monkeypatch, datafiles):
        folder_path = datafiles
        runner = CliRunner()
        if self.__test_id is None:
            self.__test_id = '70ed01da-f291-4e29-b75c-1f7977edf252'
        result_upload = runner.invoke(project, ['--path', folder_path, 'upload'])
        assert_success(result_upload)

    @pytest.mark.datafiles('tests/neoload_projects/example_1/everything.yaml')
    def test_upload(self, monkeypatch, datafiles):
        yaml_file_path = datafiles.listdir()[0]
        runner = CliRunner()
        if self.__test_id is None:
            self.__test_id = '70ed01da-f291-4e29-b75c-1f7977edf252'
        result_upload = runner.invoke(project, ['--path', yaml_file_path, 'upload'])
        assert_success(result_upload)

    @pytest.mark.datafiles('tests/neoload_projects/example_1.zip')
    def test_upload(self, monkeypatch, datafiles):
        zip_file_path = datafiles.listdir()[0]
        runner = CliRunner()
        if self.__test_id is None:
            self.__test_id = '70ed01da-f291-4e29-b75c-1f7977edf252'
        result_upload = runner.invoke(project, ['--path', zip_file_path, 'upload'])
        assert_success(result_upload)


    @pytest.mark.datafiles('tests/neoload_projects/example_1/everything.yaml')
    def test_validate(self, datafiles):
        file_path = datafiles.listdir()[0]
        runner = CliRunner()
        result = runner.invoke(validate, [str(file_path), '--refresh'])
        assert_success(result)
        assert 'Yaml file is valid' in str(result.output)

    def test_run(self):
        runner = CliRunner()
        result = runner.invoke(run, ['--as-code', ''])
        assert_success(result)
        json_run = json.loads(result.output)
        self.__result_id = json_run['id']


    def test_stop(self, monkeypatch):
        runner = CliRunner()
        if self.__result_id is None:
            self.__result_id = '70ed01da-f291-4e29-b75c-1f7977edf252'
        mock_api_post(monkeypatch, 'v2/test-results/%s/stop' % self.__result_id,
                             '{"id":"5e5fc0102cc4f82e5d9e18d4", "name":"Project", "description":"",'
                             '"scenarioName":"sanityScenario", "controllerZoneId":"a-zone", '
                             '"lgZoneIds":{"a-zone":5}, "testResultNamingPattern":"#${runId}"}')
        result = runner.invoke(stop)
        assert_success(result)
        json_stop = json.loads(result.output)
