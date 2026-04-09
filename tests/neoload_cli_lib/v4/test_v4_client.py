import pytest
from requests import Response
from neoload_cli_lib import rest_crud, user_data, cli_exception
from neoload_cli_lib.v4 import v4_client


MOCK_WORKSPACE_ID = '5e3acde2e860a132744ca916'


def _mock_workspace(monkeypatch):
    """Set up workspace mock for all workspace-aware tests."""
    monkeypatch.setattr(user_data, 'get_meta',
                        lambda key: MOCK_WORKSPACE_ID if key == 'workspace id' else None)


def _mock_no_workspace(monkeypatch):
    """Set up workspace mock to return None (no workspace set)."""
    monkeypatch.setattr(user_data, 'get_meta', lambda key: None)


def _make_response(status_code, content=b''):
    """Create a mock requests.Response."""
    response = Response()
    response.status_code = status_code
    response._content = content
    return response


@pytest.mark.usefixtures("neoload_login")
class TestV4List:
    def test_v4_list_single_page(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        monkeypatch.setattr(rest_crud, 'get',
                            lambda endpoint, params: {
                                'items': [{'id': '1', 'name': 'test1'}],
                                'total': 1,
                                'pageNumber': 0,
                                'pageSize': 200
                            })
        result = v4_client.v4_list('tests')
        assert result == [{'id': '1', 'name': 'test1'}]

    def test_v4_list_multi_page(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        call_count = {'n': 0}
        def mock_get(endpoint, params):
            page = call_count['n']
            call_count['n'] += 1
            if page == 0:
                return {'items': [{'id': '1'}, {'id': '2'}], 'total': 3, 'pageNumber': 0, 'pageSize': 2}
            else:
                return {'items': [{'id': '3'}], 'total': 3, 'pageNumber': 1, 'pageSize': 2}
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        result = v4_client.v4_list('tests')
        assert len(result) == 3
        assert result[0]['id'] == '1'
        assert result[1]['id'] == '2'
        assert result[2]['id'] == '3'

    def test_v4_list_empty(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        monkeypatch.setattr(rest_crud, 'get',
                            lambda endpoint, params: {
                                'items': [], 'total': 0, 'pageNumber': 0, 'pageSize': 200
                            })
        result = v4_client.v4_list('tests')
        assert result == []

    def test_v4_list_injects_workspace_as_query_param(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        def mock_get(endpoint, params):
            captured.update(params)
            return {'items': [], 'total': 0, 'pageNumber': 0, 'pageSize': 200}
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        v4_client.v4_list('tests')
        assert captured['workspaceId'] == MOCK_WORKSPACE_ID

    def test_v4_list_passes_page_params(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        def mock_get(endpoint, params):
            captured.update(params)
            return {'items': [], 'total': 0, 'pageNumber': 0, 'pageSize': 200}
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        v4_client.v4_list('tests')
        assert captured['pageNumber'] == 0
        assert captured['pageSize'] == 200

    def test_v4_list_merges_caller_params(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured = {}
        def mock_get(endpoint, params):
            captured.update(params)
            return {'items': [], 'total': 0, 'pageNumber': 0, 'pageSize': 200}
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        v4_client.v4_list('tests', params={'status': 'RUNNING'})
        assert captured['status'] == 'RUNNING'
        assert captured['workspaceId'] == MOCK_WORKSPACE_ID

    def test_v4_list_raises_when_no_workspace(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_no_workspace(monkeypatch)
        with pytest.raises(cli_exception.CliException) as exc_info:
            v4_client.v4_list('tests')
        assert 'No workspace set' in str(exc_info.value)

    def test_v4_list_variadic_path(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured_endpoint = {}
        def mock_get(endpoint, params):
            captured_endpoint['ep'] = endpoint
            return {'items': [], 'total': 0, 'pageNumber': 0, 'pageSize': 200}
        monkeypatch.setattr(rest_crud, 'get', mock_get)
        v4_client.v4_list('tests', '123', 'scenarios')
        assert captured_endpoint['ep'] == 'v4/tests/123/scenarios'


@pytest.mark.usefixtures("neoload_login")
class TestV4Get:
    def test_v4_get_single_resource(self, monkeypatch):
        if monkeypatch is None:
            return
        expected = {'id': '123', 'name': 'mytest'}
        monkeypatch.setattr(rest_crud, 'get',
                            lambda endpoint, params=None: expected if endpoint == 'v4/tests/123' else None)
        result = v4_client.v4_get('tests', '123')
        assert result == expected


@pytest.mark.usefixtures("neoload_login")
class TestV4Create:
    def test_v4_create_posts_with_workspace_in_body(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured_data = {}
        def mock_post(endpoint, data):
            captured_data.update(data)
            return {'id': 'new-id', **data}
        monkeypatch.setattr(rest_crud, 'post', mock_post)
        v4_client.v4_create('tests', data={'name': 'mytest'})
        assert captured_data['workspaceId'] == MOCK_WORKSPACE_ID
        assert captured_data['name'] == 'mytest'

    def test_v4_create_raises_when_no_workspace(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_no_workspace(monkeypatch)
        with pytest.raises(cli_exception.CliException) as exc_info:
            v4_client.v4_create('tests', data={'name': 'mytest'})
        assert 'No workspace set' in str(exc_info.value)

    def test_v4_create_variadic_path(self, monkeypatch):
        if monkeypatch is None:
            return
        _mock_workspace(monkeypatch)
        captured_endpoint = {}
        def mock_post(endpoint, data):
            captured_endpoint['ep'] = endpoint
            return {'id': 'new-id'}
        monkeypatch.setattr(rest_crud, 'post', mock_post)
        v4_client.v4_create('tests', '123', 'scenarios', data={'name': 'sc1'})
        assert captured_endpoint['ep'] == 'v4/tests/123/scenarios'


@pytest.mark.usefixtures("neoload_login")
class TestV4Update:
    def test_v4_update_patches(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_patch(endpoint, data):
            captured['ep'] = endpoint
            captured['data'] = data
            return {'id': '123', **data}
        monkeypatch.setattr(rest_crud, 'patch', mock_patch)
        v4_client.v4_update('tests', '123', data={'name': 'new'})
        assert captured['ep'] == 'v4/tests/123'
        assert captured['data'] == {'name': 'new'}
        assert 'workspaceId' not in captured['data']


@pytest.mark.usefixtures("neoload_login")
class TestV4Replace:
    def test_v4_replace_puts(self, monkeypatch):
        if monkeypatch is None:
            return
        captured = {}
        def mock_put(endpoint, data):
            captured['ep'] = endpoint
            captured['data'] = data
            return {'id': '123', **data}
        monkeypatch.setattr(rest_crud, 'put', mock_put)
        v4_client.v4_replace('tests', '123', data={'name': 'full'})
        assert captured['ep'] == 'v4/tests/123'
        assert captured['data'] == {'name': 'full'}


@pytest.mark.usefixtures("neoload_login")
class TestV4Delete:
    def test_v4_delete_returns_json_when_body_present(self, monkeypatch):
        if monkeypatch is None:
            return
        import json
        body = json.dumps({'status': 'deleted'}).encode()
        monkeypatch.setattr(rest_crud, 'delete',
                            lambda endpoint: _make_response(200, body))
        result = v4_client.v4_delete('tests', '123')
        assert result == {'status': 'deleted'}

    def test_v4_delete_returns_none_for_empty_202(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'delete',
                            lambda endpoint: _make_response(202, b''))
        result = v4_client.v4_delete('tests', '123')
        assert result is None

    def test_v4_delete_returns_none_for_204(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'delete',
                            lambda endpoint: _make_response(204, b''))
        result = v4_client.v4_delete('tests', '123')
        assert result is None
