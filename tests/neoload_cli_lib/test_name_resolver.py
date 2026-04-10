"""
Tests for neoload_cli_lib/name_resolver.py

Coverage targets (lines missing before these tests):
  35-43 : resolve_name_or_json() — both the found-json and not-found branches
  46-49 : get_map() — when cache is empty, triggers __fill_map then returns
"""
import pytest
from neoload_cli_lib import name_resolver, rest_crud, cli_exception


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_resolver(monkeypatch, elements, workspace='ws1'):
    """Return a Resolver whose REST calls are mocked to return *elements*."""
    monkeypatch.setattr(rest_crud, 'get_workspace', lambda: workspace)
    monkeypatch.setattr(
        rest_crud, 'get_with_pagination',
        lambda endpoint, api_query_params=None: elements
    )
    monkeypatch.setattr(rest_crud, 'put_resolved_map', lambda key, ws_map: None, raising=False)

    from neoload_cli_lib import user_data
    monkeypatch.setattr(user_data, 'put_resolved_map', lambda key, ws_map, save=True: None)

    resolver = name_resolver.Resolver(
        endpoint='/zones',
        get_base_endpoint=lambda: 'v3/workspaces/' + workspace,
        meta_key='zone id',
    )
    return resolver


_ELEMENTS = [
    {'id': 'id-alpha', 'name': 'alpha'},
    {'id': 'id-beta',  'name': 'beta'},
    {'id': 'id-gamma', 'name': 'gamma'},
]


# ---------------------------------------------------------------------------
# resolve_name() — already partially covered; add edge cases
# ---------------------------------------------------------------------------

class TestResolveName:
    def test_resolve_known_name_returns_id(self, monkeypatch):
        if monkeypatch is None:
            return
        resolver = _make_resolver(monkeypatch, _ELEMENTS)
        assert resolver.resolve_name('alpha') == 'id-alpha'

    def test_resolve_unknown_name_raises(self, monkeypatch):
        if monkeypatch is None:
            return
        resolver = _make_resolver(monkeypatch, _ELEMENTS)
        with pytest.raises(cli_exception.CliException) as exc_info:
            resolver.resolve_name('nonexistent')
        assert 'nonexistent' in str(exc_info.value.format_message())

    def test_resolve_unknown_name_return_none(self, monkeypatch):
        if monkeypatch is None:
            return
        resolver = _make_resolver(monkeypatch, _ELEMENTS)
        result = resolver.resolve_name('nonexistent', return_none=True)
        assert result is None

    def test_resolve_cached_name_skips_fill(self, monkeypatch):
        """Second call uses the in-memory cache — __fill_map is not called again."""
        if monkeypatch is None:
            return
        call_count = [0]

        def counting_pagination(endpoint, api_query_params=None):
            call_count[0] += 1
            return _ELEMENTS

        monkeypatch.setattr(rest_crud, 'get_workspace', lambda: 'ws1')
        monkeypatch.setattr(rest_crud, 'get_with_pagination', counting_pagination)
        from neoload_cli_lib import user_data
        monkeypatch.setattr(user_data, 'put_resolved_map', lambda key, ws_map, save=True: None)

        resolver = name_resolver.Resolver('/zones', lambda: 'v3/workspaces/ws1', 'zone id')
        resolver.resolve_name('alpha')   # fills cache
        resolver.resolve_name('beta')    # should use cache
        assert call_count[0] == 1        # fill called only once


# ---------------------------------------------------------------------------
# resolve_name_or_json() — lines 35-43
# ---------------------------------------------------------------------------

class TestResolveNameOrJson:
    def test_returns_full_json_when_found(self, monkeypatch):
        """When the name matches an element, the full element dict is returned (line 39-40)."""
        if monkeypatch is None:
            return
        resolver = _make_resolver(monkeypatch, _ELEMENTS)
        result = resolver.resolve_name_or_json('beta')
        assert isinstance(result, dict)
        assert result['id'] == 'id-beta'
        assert result['name'] == 'beta'

    def test_returns_full_json_for_first_element(self, monkeypatch):
        if monkeypatch is None:
            return
        resolver = _make_resolver(monkeypatch, _ELEMENTS)
        result = resolver.resolve_name_or_json('alpha')
        assert result['id'] == 'id-alpha'

    def test_raises_when_name_not_found(self, monkeypatch):
        """When no element matches, CliException is raised (line 42)."""
        if monkeypatch is None:
            return
        resolver = _make_resolver(monkeypatch, _ELEMENTS)
        with pytest.raises(cli_exception.CliException) as exc_info:
            resolver.resolve_name_or_json('no_such_name')
        assert 'no_such_name' in str(exc_info.value.format_message())

    def test_returns_cached_id_when_already_resolved(self, monkeypatch):
        """If the name was already resolved to an id (in the map), return the id directly (line 36)."""
        if monkeypatch is None:
            return
        resolver = _make_resolver(monkeypatch, _ELEMENTS)
        # Pre-warm the cache via resolve_name
        id1 = resolver.resolve_name('gamma')
        assert id1 == 'id-gamma'
        # Now resolve_name_or_json should return the id (not the full json) from cache
        result = resolver.resolve_name_or_json('gamma')
        assert result == 'id-gamma'


# ---------------------------------------------------------------------------
# get_map() — lines 46-49
# ---------------------------------------------------------------------------

class TestGetMap:
    def test_get_map_triggers_fill_when_empty(self, monkeypatch):
        """get_map() calls __fill_map when the workspace map is empty (lines 47-48)."""
        if monkeypatch is None:
            return
        resolver = _make_resolver(monkeypatch, _ELEMENTS)
        ws_map = resolver.get_map()
        assert isinstance(ws_map, dict)
        assert 'alpha' in ws_map
        assert ws_map['alpha'] == 'id-alpha'
        assert 'beta' in ws_map
        assert 'gamma' in ws_map

    def test_get_map_returns_cached_map_on_second_call(self, monkeypatch):
        """Second call must use the cached map without re-fetching."""
        if monkeypatch is None:
            return
        call_count = [0]

        def counting_pagination(endpoint, api_query_params=None):
            call_count[0] += 1
            return _ELEMENTS

        monkeypatch.setattr(rest_crud, 'get_workspace', lambda: 'ws1')
        monkeypatch.setattr(rest_crud, 'get_with_pagination', counting_pagination)
        from neoload_cli_lib import user_data
        monkeypatch.setattr(user_data, 'put_resolved_map', lambda key, ws_map, save=True: None)

        resolver = name_resolver.Resolver('/zones', lambda: 'v3/workspaces/ws1', 'zone id')
        resolver.get_map()
        resolver.get_map()
        assert call_count[0] == 1

    def test_get_map_empty_elements(self, monkeypatch):
        """get_map() with zero elements returns an empty dict."""
        if monkeypatch is None:
            return
        resolver = _make_resolver(monkeypatch, [])
        ws_map = resolver.get_map()
        assert ws_map == {}


# ---------------------------------------------------------------------------
# get_endpoint() helper
# ---------------------------------------------------------------------------

class TestGetEndpoint:
    def test_get_endpoint_concatenates_base_and_path(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'get_workspace', lambda: 'ws1')
        resolver = name_resolver.Resolver(
            endpoint='/zones',
            get_base_endpoint=lambda: 'v3/workspaces/ws1',
            meta_key='zone id',
        )
        assert resolver.get_endpoint() == 'v3/workspaces/ws1/zones'
