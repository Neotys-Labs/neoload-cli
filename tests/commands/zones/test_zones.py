import pytest
from click.testing import CliRunner
from commands.zones import cli as zones
from tests.helpers.test_utils import *


@pytest.mark.zones
@pytest.mark.makelivecalls
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestZones:
    def test_list_all(self, monkeypatch):
        runner = CliRunner()
        # mock_api_get_with_pagination(monkeypatch, 'v3/resources/zones',
        #              '[{"id": "defaultzone","name": "Default zone","type": "STATIC","controllers": [],"loadgenerators": []}]')
        result = runner.invoke(zones)
        assert_success(result)
        json_result = json.loads(result.output)
        assert len(json_result) > 1, "Was expecting more than one zone in the target environment"

    def test_list_one(self, monkeypatch):
        runner = CliRunner()
        # mock_api_get_with_pagination(monkeypatch, 'v3/resources/zones',
        #              '[{"id": "defaultzone","name": "Default zone","type": "STATIC","controllers": [],"loadgenerators": []}]')
        result = runner.invoke(zones,['defaultzone'])
        assert_success(result)
        json_result = json.loads(result.output)
        assert len(json_result) == 1, "Was expecting only one zone to come back from a single named zone listing"
        assert json_result[0]['id'] == 'defaultzone'

    def test_list_static(self, monkeypatch):
        runner = CliRunner()
        result = runner.invoke(zones,['--static'])
        assert_success(result)
        json_result = json.loads(result.output)
        assert len(json_result) > 0, "Was expecting at least one STATIC zone in the target environment"

    def test_list_dynamic(self, monkeypatch):
        runner = CliRunner()
        result = runner.invoke(zones,['--dynamic'])
        assert_success(result)
        json_result = json.loads(result.output)
        assert len(json_result) > 0, "Was expecting at least one DYNATIC zone in the target environment"

    def test_list_human(self, monkeypatch):
        runner = CliRunner()
        result = runner.invoke(zones,['-h'])
        assert_success(result)
        assert 'TYPE	ID	NAME' in result.output, "Did not find column names in human-friendly output"
        assert 'Controllers (' in result.output, "Did not find any zones with controller count information"
        assert 'Load Generator (' in result.output, "Did not find any zones with load generator count information"
