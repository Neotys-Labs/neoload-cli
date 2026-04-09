"""
Advanced tests for the v4 foundation package (v4_endpoints + v4_client).

These tests cover gaps not addressed by the initial test suite:
  - v4_endpoint: zero segments, float coercion, multiple integer segments
  - v4_workspace_params: exact key name, error message hint text
  - v4_inject_workspace: empty dict, overwrite behaviour, shallow-copy, error message hint
  - v4_list: WR-01/WR-02 known bugs documented, three-page scenario, endpoint correctness,
             pageNumber increment, missing 'items' key
  - v4_get: multi-segment path, workspace-independence, pass-through return value
  - v4_create: original dict not mutated, return value pass-through, keyword-only data arg
  - v4_update: 3-segment path, no workspaceId injection, return value pass-through
  - v4_replace: variadic path, no workspaceId injection, return value pass-through
  - v4_delete: variadic path, 200 with empty content, 202 with JSON body, endpoint delegation
"""

import json
import pytest
from requests import Response

from neoload_cli_lib import rest_crud, user_data, cli_exception
from neoload_cli_lib.v4 import v4_endpoints, v4_client


MOCK_WORKSPACE_ID = '5e3acde2e860a132744ca916'


# ---------------------------------------------------------------------------
# Helpers (mirrors the pattern used in test_v4_client.py)
# ---------------------------------------------------------------------------

def _mock_workspace(monkeypatch):
    monkeypatch.setattr(
        user_data, 'get_meta',
        lambda key: MOCK_WORKSPACE_ID if key == 'workspace id' else None,
    )


def _mock_no_workspace(monkeypatch):
    monkeypatch.setattr(user_data, 'get_meta', lambda key: None)


def _make_response(status_code, content=b''):
    """Create a minimal requests.Response without network I/O."""
    response = Response()
    response.status_code = status_code
    response._content = content
    return response


# ===========================================================================
# v4_endpoint — gap coverage
# ===========================================================================

@pytest.mark.usefixtures("neoload_login")
class TestV4EndpointGaps:
    def test_zero_segments_produces_v4_slash(self):
        """v4_endpoint() with no args should produce 'v4/' (trailing slash)."""
        assert v4_endpoints.v4_endpoint() == 'v4/'

    def test_float_segment_converted_to_string(self):
        """Float values in path segments must be coerced to their string repr."""
        result = v4_endpoints.v4_endpoint('items', 1.5)
        assert result == 'v4/items/1.5'

    def test_multiple_integer_segments_all_converted(self):
        """Multiple integer segments should all be stringified without error."""
        result = v4_endpoints.v4_endpoint(1, 2, 3)
        assert result == 'v4/1/2/3'


# ===========================================================================
# v4_workspace_params — gap coverage
# ===========================================================================

@pytest.mark.usefixtures("neoload_login")
class TestV4WorkspaceParamsGaps:
    def test_returned_dict_uses_camel_case_workspaceId_key(self, monkeypatch):
        """Result must use 'workspaceId' (camelCase), not 'workspace_id' or similar."""
        _mock_workspace(monkeypatch)
        result = v4_endpoints.v4_workspace_params()
        assert 'workspaceId' in result
        assert 'workspace_id' not in result
        assert 'workspaceid' not in result

    def test_error_message_hints_at_workspaces_use_command(self, monkeypatch):
        """CliException message must include 'workspaces use' so users know the fix."""
        _mock_no_workspace(monkeypatch)
        with pytest.raises(cli_exception.CliException) as exc_info:
            v4_endpoints.v4_workspace_params()
        assert 'workspaces use' in str(exc_info.value)


# ===========================================================================
# v4_inject_workspace — gap coverage
# ===========================================================================

@pytest.mark.usefixtures("neoload_login")
class TestV4InjectWorkspaceGaps:
    def test_empty_dict_input_returns_only_workspace_id(self, monkeypatch):
        """An empty payload should yield exactly {'workspaceId': <id>} — nothing more."""
        _mock_workspace(monkeypatch)
        result = v4_endpoints.v4_inject_workspace({})
        assert result == {'workspaceId': MOCK_WORKSPACE_ID}

    def test_existing_workspace_id_in_data_is_overwritten(self, monkeypatch):
        """If caller supplies 'workspaceId', the authoritative workspace replaces it."""
        _mock_workspace(monkeypatch)
        result = v4_endpoints.v4_inject_workspace({'workspaceId': 'old-wrong-id'})
        assert result['workspaceId'] == MOCK_WORKSPACE_ID

    def test_shallow_copy_means_nested_dict_is_shared(self, monkeypatch):
        """
        v4_inject_workspace uses dict() (shallow copy). A nested mutable object in the
        original is the SAME object in the result — this documents known shallow-copy behaviour.
        """
        _mock_workspace(monkeypatch)
        nested = {'key': 'value'}
        original = {'meta': nested}
        result = v4_endpoints.v4_inject_workspace(original)
        # They share the same nested dict object
        assert result['meta'] is nested

    def test_error_message_hints_at_workspaces_use_command(self, monkeypatch):
        """CliException from inject_workspace must include 'workspaces use' hint."""
        _mock_no_workspace(monkeypatch)
        with pytest.raises(cli_exception.CliException) as exc_info:
            v4_endpoints.v4_inject_workspace({'name': 'test'})
        assert 'workspaces use' in str(exc_info.value)


# ===========================================================================
# v4_list — gap coverage
# ===========================================================================

@pytest.mark.usefixtures("neoload_login")
class TestV4ListGaps:
    def test_missing_total_key_terminates_after_first_non_empty_page_wr01(self, monkeypatch):
        """
        WR-01: When the response lacks a 'total' key, response.get('total', 0) returns 0.
        Because len(all_items) >= 0 is immediately True, the loop exits after the first
        page even when items were returned. This test DOCUMENTS that bug — the result
        contains only the first page.
        """
        _mock_workspace(monkeypatch)
        call_count = {'n': 0}

        def mock_get(endpoint, params):
            call_count['n'] += 1
            # Page 0: return 2 items but omit 'total'
            return {'items': [{'id': '1'}, {'id': '2'}]}

        monkeypatch.setattr(rest_crud, 'get', mock_get)
        result = v4_client.v4_list('tests')

        # Bug WR-01: only one call is made because total defaults to 0
        assert call_count['n'] == 1
        assert result == [{'id': '1'}, {'id': '2'}]

    def test_missing_total_key_with_empty_items_terminates_immediately_wr01(self, monkeypatch):
        """
        WR-01 corollary: no 'total' key AND no items → loop exits on first iteration.
        """
        _mock_workspace(monkeypatch)
        call_count = {'n': 0}

        def mock_get(endpoint, params):
            call_count['n'] += 1
            return {}  # neither 'items' nor 'total'

        monkeypatch.setattr(rest_crud, 'get', mock_get)
        result = v4_client.v4_list('tests')

        assert call_count['n'] == 1
        assert result == []

    def test_caller_params_can_override_page_number_wr02(self, monkeypatch):
        """
        WR-02: query_params.update(params) means caller-supplied 'pageNumber'
        overrides the internal counter. This test documents that behaviour.
        """
        _mock_workspace(monkeypatch)
        captured_pages = []

        def mock_get(endpoint, params):
            captured_pages.append(params.get('pageNumber'))
            return {'items': [], 'total': 0}

        monkeypatch.setattr(rest_crud, 'get', mock_get)
        v4_client.v4_list('tests', params={'pageNumber': 99})

        assert captured_pages[0] == 99  # caller value wins

    def test_caller_params_can_override_workspace_id_wr02(self, monkeypatch):
        """
        WR-02: query_params.update(params) means caller can override 'workspaceId'.
        This test documents that — potentially unsafe — behaviour.
        """
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_get(endpoint, params):
            captured.update(params)
            return {'items': [], 'total': 0}

        monkeypatch.setattr(rest_crud, 'get', mock_get)
        v4_client.v4_list('tests', params={'workspaceId': 'caller-override'})

        assert captured['workspaceId'] == 'caller-override'

    def test_three_page_scenario_returns_all_items(self, monkeypatch):
        """
        total=5, pageSize=2: three API calls (pages 0, 1, 2) should accumulate all 5 items.
        """
        _mock_workspace(monkeypatch)
        call_count = {'n': 0}

        def mock_get(endpoint, params):
            page = call_count['n']
            call_count['n'] += 1
            pages = [
                {'items': [{'id': '1'}, {'id': '2'}], 'total': 5},
                {'items': [{'id': '3'}, {'id': '4'}], 'total': 5},
                {'items': [{'id': '5'}],               'total': 5},
            ]
            return pages[page]

        monkeypatch.setattr(rest_crud, 'get', mock_get)
        result = v4_client.v4_list('tests')

        assert call_count['n'] == 3
        assert [item['id'] for item in result] == ['1', '2', '3', '4', '5']

    def test_single_segment_endpoint_passed_to_rest_crud_get(self, monkeypatch):
        """Endpoint forwarded to rest_crud.get must be 'v4/<segment>' for a single segment."""
        _mock_workspace(monkeypatch)
        captured = {}

        def mock_get(endpoint, params):
            captured['ep'] = endpoint
            return {'items': [], 'total': 0}

        monkeypatch.setattr(rest_crud, 'get', mock_get)
        v4_client.v4_list('resources')

        assert captured['ep'] == 'v4/resources'

    def test_page_number_increments_on_each_subsequent_request(self, monkeypatch):
        """pageNumber must start at 0 and increment by 1 for each additional page."""
        _mock_workspace(monkeypatch)
        observed_pages = []

        def mock_get(endpoint, params):
            observed_pages.append(params['pageNumber'])
            # Two pages: total=3, pageSize=200 means 2 calls (page 0 returns 2 items, page 1 returns 1)
            if params['pageNumber'] == 0:
                return {'items': [{'id': 'a'}, {'id': 'b'}], 'total': 3}
            return {'items': [{'id': 'c'}], 'total': 3}

        monkeypatch.setattr(rest_crud, 'get', mock_get)
        v4_client.v4_list('tests')

        assert observed_pages == [0, 1]

    def test_returns_empty_list_when_response_has_no_items_key(self, monkeypatch):
        """If first response is missing the 'items' key, result must be an empty list."""
        _mock_workspace(monkeypatch)
        monkeypatch.setattr(rest_crud, 'get', lambda ep, params: {'total': 10})

        result = v4_client.v4_list('tests')

        assert result == []


# ===========================================================================
# v4_get — gap coverage
# ===========================================================================

@pytest.mark.usefixtures("neoload_login")
class TestV4GetGaps:
    def test_multi_segment_path_builds_correct_endpoint(self, monkeypatch):
        """v4_get with 3 segments must forward 'v4/a/b/c' to rest_crud.get."""
        captured = {}

        def mock_get(endpoint, params=None):
            captured['ep'] = endpoint
            return {}

        monkeypatch.setattr(rest_crud, 'get', mock_get)
        v4_client.v4_get('a', 'b', 'c')

        assert captured['ep'] == 'v4/a/b/c'

    def test_v4_get_does_not_call_user_data_get_meta(self, monkeypatch):
        """
        v4_get must NOT require a workspace — it should never call user_data.get_meta.
        We verify this by installing a get_meta that raises; if it is called the test fails.
        """
        def exploding_get_meta(key):
            raise AssertionError("v4_get must not access workspace metadata")

        monkeypatch.setattr(user_data, 'get_meta', exploding_get_meta)
        monkeypatch.setattr(rest_crud, 'get', lambda ep, params=None: {'id': '42'})

        # Must not raise
        result = v4_client.v4_get('tests', '42')
        assert result == {'id': '42'}

    def test_v4_get_returns_rest_crud_value_unchanged(self, monkeypatch):
        """v4_get must return exactly what rest_crud.get returns, without transformation."""
        sentinel = {'id': 'xyz', 'nested': [1, 2, 3]}
        monkeypatch.setattr(rest_crud, 'get', lambda ep, params=None: sentinel)

        result = v4_client.v4_get('tests', 'xyz')

        assert result is sentinel


# ===========================================================================
# v4_create — gap coverage
# ===========================================================================

@pytest.mark.usefixtures("neoload_login")
class TestV4CreateGaps:
    def test_original_data_dict_not_mutated_after_create(self, monkeypatch):
        """v4_create injects workspaceId into a copy; the caller's dict must be unchanged."""
        _mock_workspace(monkeypatch)
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: {'id': 'new', **data})

        original = {'name': 'mytest', 'description': 'a test'}
        v4_client.v4_create('tests', data=original)

        assert 'workspaceId' not in original
        assert original == {'name': 'mytest', 'description': 'a test'}

    def test_v4_create_returns_rest_crud_post_value_unchanged(self, monkeypatch):
        """v4_create must return whatever rest_crud.post returns, without modification."""
        _mock_workspace(monkeypatch)
        sentinel = {'id': 'created-123', 'workspaceId': MOCK_WORKSPACE_ID}
        monkeypatch.setattr(rest_crud, 'post', lambda ep, data: sentinel)

        result = v4_client.v4_create('tests', data={'name': 'x'})

        assert result is sentinel

    def test_v4_create_data_is_keyword_only(self):
        """
        'data' must be passed as a keyword argument. Passing it positionally should
        raise a TypeError, confirming it is keyword-only.
        """
        with pytest.raises(TypeError):
            # positional: v4_create('tests', {'name': 'x'}) is ambiguous — treated as a
            # path segment, so 'data' kwarg is missing → TypeError
            v4_client.v4_create('tests', {'name': 'x'})


# ===========================================================================
# v4_update — gap coverage
# ===========================================================================

@pytest.mark.usefixtures("neoload_login")
class TestV4UpdateGaps:
    def test_three_segment_path_builds_correct_endpoint(self, monkeypatch):
        """v4_update with 3 path segments must produce 'v4/a/b/c'."""
        captured = {}

        def mock_patch(endpoint, data):
            captured['ep'] = endpoint
            return data

        monkeypatch.setattr(rest_crud, 'patch', mock_patch)
        v4_client.v4_update('a', 'b', 'c', data={'x': 1})

        assert captured['ep'] == 'v4/a/b/c'

    def test_v4_update_does_not_inject_workspace_id_into_data(self, monkeypatch):
        """v4_update uses PATCH semantics; it must never add workspaceId to the payload."""
        captured_data = {}

        def mock_patch(endpoint, data):
            captured_data.update(data)
            return data

        monkeypatch.setattr(rest_crud, 'patch', mock_patch)
        v4_client.v4_update('tests', '123', data={'name': 'updated'})

        assert 'workspaceId' not in captured_data

    def test_v4_update_returns_rest_crud_patch_value_unchanged(self, monkeypatch):
        """v4_update must return exactly what rest_crud.patch returns."""
        sentinel = {'id': '123', 'name': 'updated'}
        monkeypatch.setattr(rest_crud, 'patch', lambda ep, data: sentinel)

        result = v4_client.v4_update('tests', '123', data={'name': 'updated'})

        assert result is sentinel


# ===========================================================================
# v4_replace — gap coverage
# ===========================================================================

@pytest.mark.usefixtures("neoload_login")
class TestV4ReplaceGaps:
    def test_variadic_path_builds_correct_endpoint(self, monkeypatch):
        """v4_replace with 3 path segments must produce 'v4/x/y/z'."""
        captured = {}

        def mock_put(endpoint, data):
            captured['ep'] = endpoint
            return data

        monkeypatch.setattr(rest_crud, 'put', mock_put)
        v4_client.v4_replace('x', 'y', 'z', data={'full': True})

        assert captured['ep'] == 'v4/x/y/z'

    def test_v4_replace_does_not_inject_workspace_id(self, monkeypatch):
        """v4_replace (PUT) must not add workspaceId to the payload it sends."""
        captured_data = {}

        def mock_put(endpoint, data):
            captured_data.update(data)
            return data

        monkeypatch.setattr(rest_crud, 'put', mock_put)
        v4_client.v4_replace('tests', '123', data={'name': 'full-name'})

        assert 'workspaceId' not in captured_data

    def test_v4_replace_returns_rest_crud_put_value_unchanged(self, monkeypatch):
        """v4_replace must return exactly what rest_crud.put returns."""
        sentinel = {'id': '123', 'name': 'full-name'}
        monkeypatch.setattr(rest_crud, 'put', lambda ep, data: sentinel)

        result = v4_client.v4_replace('tests', '123', data={'name': 'full-name'})

        assert result is sentinel


# ===========================================================================
# v4_delete — gap coverage
# ===========================================================================

@pytest.mark.usefixtures("neoload_login")
class TestV4DeleteGaps:
    def test_variadic_path_builds_correct_endpoint(self, monkeypatch):
        """v4_delete with 3 path segments must forward 'v4/a/b/c' to rest_crud.delete."""
        captured = {}

        def mock_delete(endpoint):
            captured['ep'] = endpoint
            return _make_response(204, b'')

        monkeypatch.setattr(rest_crud, 'delete', mock_delete)
        v4_client.v4_delete('a', 'b', 'c')

        assert captured['ep'] == 'v4/a/b/c'

    def test_200_with_empty_content_returns_none(self, monkeypatch):
        """
        A 200 response with no body should return None because the content check
        (response.content being falsy) takes precedence over the status code check.
        """
        monkeypatch.setattr(
            rest_crud, 'delete',
            lambda ep: _make_response(200, b''),
        )

        result = v4_client.v4_delete('tests', '123')

        assert result is None

    def test_202_with_json_body_returns_parsed_json(self, monkeypatch):
        """A 202 response with a JSON body should be parsed and returned (non-empty 202)."""
        body = json.dumps({'status': 'accepted', 'jobId': 'job-999'}).encode()
        monkeypatch.setattr(
            rest_crud, 'delete',
            lambda ep: _make_response(202, body),
        )

        result = v4_client.v4_delete('tests', '123')

        assert result == {'status': 'accepted', 'jobId': 'job-999'}

    def test_delegates_to_rest_crud_delete_with_correct_endpoint(self, monkeypatch):
        """
        v4_delete must call rest_crud.delete exactly once with the right endpoint,
        not rest_crud.get, post, patch, or put.
        """
        call_log = []

        def mock_delete(endpoint):
            call_log.append(endpoint)
            return _make_response(204, b'')

        monkeypatch.setattr(rest_crud, 'delete', mock_delete)
        # Install sentinel raises on the other methods to confirm they're not called
        monkeypatch.setattr(rest_crud, 'get',   lambda *a, **kw: (_ for _ in ()).throw(AssertionError("get called")))
        monkeypatch.setattr(rest_crud, 'post',  lambda *a, **kw: (_ for _ in ()).throw(AssertionError("post called")))
        monkeypatch.setattr(rest_crud, 'patch', lambda *a, **kw: (_ for _ in ()).throw(AssertionError("patch called")))
        monkeypatch.setattr(rest_crud, 'put',   lambda *a, **kw: (_ for _ in ()).throw(AssertionError("put called")))

        v4_client.v4_delete('resources', 'abc')

        assert call_log == ['v4/resources/abc']
