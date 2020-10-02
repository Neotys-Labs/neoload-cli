import json
import pytest
from neoload_cli_lib import rest_crud


@pytest.mark.results
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestRestCrud:
    def test_get_with_pagination(self, monkeypatch):
        if monkeypatch is None:
            print('SKIPPED')
            return
        all_entries = self.call_get_with_pagination(monkeypatch, 5, 5, is_implemented_in_api=True)
        assert len(all_entries) == 5
        assert all_entries[0]['id'] == '0'
        assert all_entries[1]['id'] == '1'
        assert all_entries[2]['id'] == '2'
        assert all_entries[3]['id'] == '3'
        assert all_entries[4]['id'] == '4'

        all_entries = self.call_get_with_pagination(monkeypatch, 2, 6, is_implemented_in_api=True)
        assert len(all_entries) == 6
        assert all_entries[0]['id'] == '0'
        assert all_entries[1]['id'] == '1'
        assert all_entries[2]['id'] == '2'
        assert all_entries[3]['id'] == '3'
        assert all_entries[4]['id'] == '4'
        assert all_entries[5]['id'] == '5'

        all_entries = self.call_get_with_pagination(monkeypatch, 10, 5, is_implemented_in_api=True)
        assert len(all_entries) == 5
        assert all_entries[0]['id'] == '0'
        assert all_entries[1]['id'] == '1'
        assert all_entries[2]['id'] == '2'
        assert all_entries[3]['id'] == '3'
        assert all_entries[4]['id'] == '4'

        all_entries = self.call_get_with_pagination(monkeypatch, 10, 0, is_implemented_in_api=True)
        assert len(all_entries) == 0

    # Test the case when the pagination is not implemented in the API (get endpoint always return all elements)
    def test_get_with_pagination_not_implem(self, monkeypatch):
        if monkeypatch is None:
            print('SKIPPED')
            return
        all_entries = self.call_get_with_pagination(monkeypatch, 5, 5, is_implemented_in_api=False)
        assert len(all_entries) == 5
        assert all_entries[0]['id'] == '0'
        assert all_entries[1]['id'] == '1'
        assert all_entries[2]['id'] == '2'
        assert all_entries[3]['id'] == '3'
        assert all_entries[4]['id'] == '4'

        all_entries = self.call_get_with_pagination(monkeypatch, 2, 6, is_implemented_in_api=False)
        assert len(all_entries) == 6
        assert all_entries[0]['id'] == '0'
        assert all_entries[1]['id'] == '1'
        assert all_entries[2]['id'] == '2'
        assert all_entries[3]['id'] == '3'
        assert all_entries[4]['id'] == '4'
        assert all_entries[5]['id'] == '5'

        all_entries = self.call_get_with_pagination(monkeypatch, 10, 5, is_implemented_in_api=False)
        assert len(all_entries) == 5
        assert all_entries[0]['id'] == '0'
        assert all_entries[1]['id'] == '1'
        assert all_entries[2]['id'] == '2'
        assert all_entries[3]['id'] == '3'
        assert all_entries[4]['id'] == '4'

        all_entries = self.call_get_with_pagination(monkeypatch, 10, 0, is_implemented_in_api=False)
        assert len(all_entries) == 0

    def call_get_with_pagination(self, monkeypatch, page_size, nb_total_of_elements, is_implemented_in_api):
        if monkeypatch is not None:
            monkeypatch.setattr(rest_crud, 'get',
                                lambda actual_endpoint, actual_params: self.mock_get_return(
                                    actual_endpoint, actual_params, nb_total_of_elements, is_implemented_in_api))
        return rest_crud.get_with_pagination('/v2/test-results', page_size)

    @staticmethod
    def mock_get_return(actual_endpoint, actual_params, nb_total_of_elem, is_implemented_in_api):
        expected_endpoint = '/v2/test-results'
        if actual_endpoint == expected_endpoint:
            json_result = ''
            if is_implemented_in_api:
                page_size = actual_params['limit']
                offset = actual_params['offset']
                elements_to_return = range(nb_total_of_elem)[offset:offset + page_size]
            else:
                # actual_params are ignored (simulate no pagination in API) - always return all elements
                elements_to_return = range(nb_total_of_elem)
            for i in elements_to_return:
                json_result += f'{{"id":"{i}", "name":"a name {i}"}},'
            return json.loads('[' + json_result[:-1] + ']')
        raise Exception('Fail ! BAD endpoint.\nActual  : %s\nExpected: %s' % (actual_endpoint, expected_endpoint))
