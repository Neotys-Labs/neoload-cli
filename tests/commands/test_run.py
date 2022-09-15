import pytest
from click.testing import CliRunner
from commands.test_results import cli as results
from commands.logout import cli as logout
from commands.run import prepare_lock, prepare_external_url, create_data
from tests.helpers.test_utils import *

class TestRun:

    def test_prepare_lock (self):
        data = {}
        lock = True
        expected_data = {"isLocked": True}
        prepare_lock(data, lock)
        assert (expected_data == data) is True

    def test_prepare_external_url (self):
        data = {}
        external_url = "www.random_url.com"
        external_url_label = "label of the random url"
        expected_data = {"externalUrl": "www.random_url.com", "externalUrlLabel": "label of the random url"}
        prepare_external_url(data, external_url, external_url_label)
        assert (expected_data == data) is True
    
    def test_create_data (self):
        name = "result_13"
        description = "test_descript"
        as_code = "0"
        web_vu = "10"
        sap_vu = "10"
        citrix_vu= "10"
        reservation_duration = "1200"
        reservation_id = "resaId"
        create_data_query = create_data(name, description, as_code, web_vu, sap_vu, citrix_vu, reservation_id,
                                        reservation_duration)
        expected_query = "testResultName=result_13&testResultDescription=test_descript&asCode=0&reservationWebVUs=10" \
                         "&reservationSAPVUs=10&reservationCitrixVUs=10&reservationId=resaId&reservationDuration=1200"

        assert (create_data_query == expected_query) is True

    def test_create_data_empty(self):
        create_data_query = create_data("resultname", None, None, None, None, None, None, None)
        expected_query = "testResultName=resultname"

        assert (create_data_query == expected_query) is True