import pytest
from neoload_cli_lib import user_data, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@pytest.mark.usefixtures("neoload_login")
class TestV4Base:
    def test_v4_base_returns_v4(self):
        assert v4_endpoints.v4_base() == 'v4'


@pytest.mark.usefixtures("neoload_login")
class TestV4Endpoint:
    def test_v4_endpoint_single_segment(self):
        assert v4_endpoints.v4_endpoint('tests') == 'v4/tests'

    def test_v4_endpoint_two_segments(self):
        assert v4_endpoints.v4_endpoint('tests', '123') == 'v4/tests/123'

    def test_v4_endpoint_three_segments(self):
        assert v4_endpoints.v4_endpoint('tests', '123', 'scenarios') == 'v4/tests/123/scenarios'

    def test_v4_endpoint_four_segments(self):
        assert v4_endpoints.v4_endpoint('tests', '123', 'scenarios', '456') == 'v4/tests/123/scenarios/456'

    def test_v4_endpoint_converts_non_strings(self):
        assert v4_endpoints.v4_endpoint('tests', 123) == 'v4/tests/123'


@pytest.mark.usefixtures("neoload_login")
class TestV4WorkspaceParams:
    def test_v4_workspace_params_returns_dict(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(user_data, 'get_meta',
                            lambda key: '5e3acde2e860a132744ca916' if key == 'workspace id' else None)
        result = v4_endpoints.v4_workspace_params()
        assert result == {'workspaceId': '5e3acde2e860a132744ca916'}

    def test_v4_workspace_params_raises_when_no_workspace(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(user_data, 'get_meta', lambda key: None)
        with pytest.raises(cli_exception.CliException) as exc_info:
            v4_endpoints.v4_workspace_params()
        assert 'No workspace set' in str(exc_info.value)


@pytest.mark.usefixtures("neoload_login")
class TestV4InjectWorkspace:
    def test_v4_inject_workspace_adds_workspace_to_data(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(user_data, 'get_meta',
                            lambda key: '5e3acde2e860a132744ca916' if key == 'workspace id' else None)
        result = v4_endpoints.v4_inject_workspace({'name': 'test'})
        assert result == {'name': 'test', 'workspaceId': '5e3acde2e860a132744ca916'}

    def test_v4_inject_workspace_does_not_mutate_original(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(user_data, 'get_meta',
                            lambda key: '5e3acde2e860a132744ca916' if key == 'workspace id' else None)
        original = {'name': 'test'}
        v4_endpoints.v4_inject_workspace(original)
        assert 'workspaceId' not in original

    def test_v4_inject_workspace_raises_when_no_workspace(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(user_data, 'get_meta', lambda key: None)
        with pytest.raises(cli_exception.CliException) as exc_info:
            v4_endpoints.v4_inject_workspace({'name': 'test'})
        assert 'No workspace set' in str(exc_info.value)
