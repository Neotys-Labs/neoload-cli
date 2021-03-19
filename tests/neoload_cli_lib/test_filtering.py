from neoload_cli_lib import filtering


class TestFiltering:
    def test_parse_filters(self):
        (api_query_params, cli_params) = filtering.parse_filters('name=toto;description=a word', ['name'])
        assert len(api_query_params) == 1
        assert api_query_params['name'] == 'toto'
        assert len(cli_params) == 1
        assert cli_params['description'] == 'a word'

    def test_remove_by_filter(self):
        cli_params = {'description': 'a word', 'int': '6'}
        all_elements = [{"id": "someId", "name": "elementWithouDescription"},
                        {"id": "someId", "name": "toto", "description": "a word", "int": 6},
                        {"id": "someId", "name": "notMe", "description": ".... "},
                        {"id": "someId", "name": "numeric", "int": 5}]
        filtered_elements = filtering.remove_by_filter(all_elements, cli_params)
        assert len(filtered_elements) == 1
        assert filtered_elements[0] == {"id": "someId", "name": "toto", "description": "a word", "int": 6}
