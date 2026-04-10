import json
import sys
import pytest
from unittest.mock import MagicMock
from requests import Response
from neoload_cli_lib import rest_crud, cli_exception


# ---------------------------------------------------------------------------
# Helper to build a minimal fake Response object
# ---------------------------------------------------------------------------

def _make_response(status_code, body_text='{"key": "value"}', apparent_encoding='utf-8'):
    resp = Response()
    resp.status_code = status_code
    resp._content = body_text.encode('utf-8')
    resp.encoding = apparent_encoding
    # give it a fake request so __handle_error can read .request.method / .request.url
    fake_request = MagicMock()
    fake_request.method = 'GET'
    fake_request.url = 'https://api.example.com/v2/test'
    resp.request = fake_request
    return resp


def _make_fake_user_data(url='https://api.example.com/', token='tok', file_storage='https://files.example.com/'):
    ud = MagicMock()
    ud.get_url.return_value = url
    ud.get_token.return_value = token
    ud.get_file_storage_url.return_value = file_storage
    return ud


# ---------------------------------------------------------------------------
# Existing tests (unchanged)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# New unit tests — all calls mocked, no real network
# ---------------------------------------------------------------------------

class TestCustomParseRetryAfter:
    """Tests for custom_parse_retry_after (lines 48-51)."""

    def test_positive_retry_after_converts_ms_to_seconds(self):
        result = rest_crud.custom_parse_retry_after('2000')
        assert result == 2.0

    def test_zero_retry_after_returns_zero(self):
        result = rest_crud.custom_parse_retry_after('0')
        assert result == 0

    def test_small_value_converts_correctly(self):
        result = rest_crud.custom_parse_retry_after('500')
        assert result == 0.5


class TestHandleError:
    """Tests for __handle_error — accessed indirectly via public functions (lines 172-184)."""

    def test_2xx_response_passes_through(self, monkeypatch):
        if monkeypatch is None:
            return
        resp = _make_response(200, '{"ok": true}')
        # Call get() which internally calls __handle_error via get_raw
        monkeypatch.setattr(rest_crud, 'get_raw', lambda ep, params=None: resp)
        result = rest_crud.get('v2/test')
        assert result == {'ok': True}

    def test_401_raises_access_denied(self, monkeypatch):
        if monkeypatch is None:
            return
        resp = _make_response(401, 'Unauthorized')
        monkeypatch.setattr(rest_crud, 'get_raw', lambda ep, params=None: resp)
        with pytest.raises(cli_exception.CliException) as exc_info:
            rest_crud.get('v2/test')
        assert '401' in str(exc_info.value.format_message())

    def test_500_raises_error_with_status_code(self, monkeypatch):
        if monkeypatch is None:
            return
        resp = _make_response(500, 'Internal Server Error')
        monkeypatch.setattr(rest_crud, 'get_raw', lambda ep, params=None: resp)
        with pytest.raises(cli_exception.CliException) as exc_info:
            rest_crud.get('v2/test')
        assert '500' in str(exc_info.value.format_message())

    def test_404_raises_error_with_status_code(self, monkeypatch):
        if monkeypatch is None:
            return
        resp = _make_response(404, 'Not found')
        monkeypatch.setattr(rest_crud, 'get_raw', lambda ep, params=None: resp)
        with pytest.raises(cli_exception.CliException) as exc_info:
            rest_crud.get('v2/test')
        assert '404' in str(exc_info.value.format_message())


class TestGetAndGetRaw:
    """Tests for get() and get_raw() (lines 90, and via http mock)."""

    def test_get_calls_handle_error_and_returns_json(self, monkeypatch):
        if monkeypatch is None:
            return
        resp = _make_response(200, '{"items": [1, 2]}')
        monkeypatch.setattr(rest_crud, 'get_raw', lambda ep, params=None: resp)
        result = rest_crud.get('v2/items')
        assert result == {'items': [1, 2]}

    def test_get_raw_uses_http_session(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)

        resp = _make_response(200, '{"result": "ok"}')
        monkeypatch.setattr(rest_crud.http, 'get', lambda url, params=None, headers=None, verify=None: resp)
        raw = rest_crud.get_raw('v2/items', params={'limit': 10})
        assert raw.status_code == 200


class TestPost:
    """Tests for post() (lines 99-103)."""

    def test_post_returns_json_on_success(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)

        resp = _make_response(201, '{"id": "abc123"}')
        monkeypatch.setattr(rest_crud.http, 'post',
                            lambda url, headers=None, json=None, verify=None: resp)
        result = rest_crud.post('v2/tests', {'name': 'my test'})
        assert result == {'id': 'abc123'}

    def test_post_raises_on_error(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)

        resp = _make_response(400, 'Bad Request')
        monkeypatch.setattr(rest_crud.http, 'post',
                            lambda url, headers=None, json=None, verify=None: resp)
        with pytest.raises(cli_exception.CliException) as exc_info:
            rest_crud.post('v2/tests', {})
        assert '400' in str(exc_info.value.format_message())


class TestPut:
    """Tests for put() (lines 145-149)."""

    def test_put_returns_json_on_success(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)

        resp = _make_response(200, '{"updated": true}')
        monkeypatch.setattr(rest_crud.http, 'put',
                            lambda url, headers=None, json=None, verify=None: resp)
        result = rest_crud.put('v2/tests/abc', {'name': 'updated'})
        assert result == {'updated': True}

    def test_put_raises_on_error(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)

        resp = _make_response(422, 'Unprocessable')
        monkeypatch.setattr(rest_crud.http, 'put',
                            lambda url, headers=None, json=None, verify=None: resp)
        with pytest.raises(cli_exception.CliException):
            rest_crud.put('v2/tests/abc', {})


class TestPatch:
    """Tests for patch() (lines 153-157)."""

    def test_patch_returns_json_on_success(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)

        resp = _make_response(200, '{"patched": true}')
        monkeypatch.setattr(rest_crud.http, 'patch',
                            lambda url, headers=None, json=None, verify=None: resp)
        result = rest_crud.patch('v2/tests/abc', {'field': 'val'})
        assert result == {'patched': True}

    def test_patch_raises_on_error(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)

        resp = _make_response(500, 'Server Error')
        monkeypatch.setattr(rest_crud.http, 'patch',
                            lambda url, headers=None, json=None, verify=None: resp)
        with pytest.raises(cli_exception.CliException):
            rest_crud.patch('v2/tests/abc', {})


class TestDelete:
    """Tests for delete() (lines 161-164)."""

    def test_delete_returns_response_on_success(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)

        resp = _make_response(204, '')
        resp._content = b''
        monkeypatch.setattr(rest_crud.http, 'delete',
                            lambda url, headers=None, verify=None: resp)
        result = rest_crud.delete('v2/tests/abc')
        assert result.status_code == 204

    def test_delete_raises_on_error(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)

        resp = _make_response(404, 'Not found')
        monkeypatch.setattr(rest_crud.http, 'delete',
                            lambda url, headers=None, verify=None: resp)
        with pytest.raises(cli_exception.CliException):
            rest_crud.delete('v2/tests/abc')


class TestFileStorageFunctions:
    """Tests for file-storage related functions (lines 107, 111, 116-125, 129-141)."""

    def test_get_from_file_storage_returns_response(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)

        resp = _make_response(200, '{"files": []}')
        monkeypatch.setattr(rest_crud.http, 'get',
                            lambda url, headers=None, verify=None: resp)
        result = rest_crud.get_from_file_storage('upload/project')
        assert result.status_code == 200

    def test_get_from_file_storage_raises_on_error(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)

        resp = _make_response(403, 'Forbidden')
        monkeypatch.setattr(rest_crud.http, 'get',
                            lambda url, headers=None, verify=None: resp)
        with pytest.raises(cli_exception.CliException):
            rest_crud.get_from_file_storage('upload/project')

    def test_multipart_progress_non_interactive(self, monkeypatch, tmp_path):
        """Non-interactive mode returns (encoder, None) — covers lines 140-141."""
        if monkeypatch is None:
            return
        from neoload_cli_lib import tools
        monkeypatch.setattr(tools, 'is_user_interactive', lambda: False)

        # Create a small real file so MultipartEncoder can open it
        test_file = tmp_path / 'payload.txt'
        test_file.write_bytes(b'hello world')

        with open(str(test_file), 'rb') as fh:
            encoder, bar = rest_crud.multipart_progress(fh, 'payload.txt')
        assert bar is None
        assert encoder is not None

    def test_multipart_progress_interactive(self, monkeypatch, tmp_path):
        """Interactive mode returns (monitor, bar) — covers lines 131-139."""
        if monkeypatch is None:
            return
        from neoload_cli_lib import tools
        monkeypatch.setattr(tools, 'is_user_interactive', lambda: True)

        test_file = tmp_path / 'payload.txt'
        test_file.write_bytes(b'hello world')

        with open(str(test_file), 'rb') as fh:
            monitor, bar = rest_crud.multipart_progress(fh, 'payload.txt')
        assert bar is not None
        bar.close()

    def test_post_binary_files_storage_success(self, monkeypatch, tmp_path):
        """Covers lines 116-125 (non-interactive: bar is None, bar.close() not called)."""
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data, tools
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)
        monkeypatch.setattr(tools, 'is_user_interactive', lambda: False)

        test_file = tmp_path / 'project.zip'
        test_file.write_bytes(b'PK binary content')

        resp = _make_response(200, '{"id": "upload1"}')
        monkeypatch.setattr(rest_crud.http, 'post',
                            lambda url, headers=None, data=None, verify=None: resp)

        with open(str(test_file), 'rb') as fh:
            result = rest_crud.post_binary_files_storage('upload/project', fh, 'project.zip')
        assert result.status_code == 200

    def test_post_binary_files_storage_interactive_closes_bar(self, monkeypatch, tmp_path):
        """Covers line 123: bar.close() is called when interactive mode is active."""
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data, tools
        fake_ud = _make_fake_user_data()
        monkeypatch.setattr(user_data, 'get_user_data', lambda: fake_ud)
        monkeypatch.setattr(user_data, 'get_ssl_cert', lambda: False)
        # Interactive mode → multipart_progress returns (monitor, bar)
        monkeypatch.setattr(tools, 'is_user_interactive', lambda: True)

        test_file = tmp_path / 'upload.bin'
        test_file.write_bytes(b'binary data')

        resp = _make_response(200, '{"id": "upload2"}')
        monkeypatch.setattr(rest_crud.http, 'post',
                            lambda url, headers=None, data=None, verify=None: resp)

        bar_close_called = []
        original_multipart_progress = rest_crud.multipart_progress

        def fake_multipart_progress(path, filename):
            monitor, bar = original_multipart_progress(path, filename)
            # Wrap bar.close to track the call
            original_close = bar.close
            bar.close = lambda: bar_close_called.append(True) or original_close()
            return monitor, bar

        monkeypatch.setattr(rest_crud, 'multipart_progress', fake_multipart_progress)

        with open(str(test_file), 'rb') as fh:
            result = rest_crud.post_binary_files_storage('upload/project', fh, 'upload.bin')
        assert result.status_code == 200
        assert len(bar_close_called) == 1, "bar.close() must be called when bar is not None"


class TestAddUserAgent:
    """Tests for add_user_agent() (lines 197-204)."""

    def test_user_agent_added_first_time(self, monkeypatch):
        if monkeypatch is None:
            return
        # Module-level dunder vars are accessed via their actual names (no name mangling at module scope)
        monkeypatch.setattr(rest_crud, '__agents_already_sent', set())
        monkeypatch.setattr(rest_crud, '__current_command', 'testcmd')
        monkeypatch.setattr(rest_crud, '__current_sub_command', 'sub')

        headers = {}
        rest_crud.add_user_agent(headers)
        assert 'User-Agent' in headers
        assert 'NeoloadCli/' in headers['User-Agent']

    def test_user_agent_not_duplicated_second_call(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, '__agents_already_sent', set())
        monkeypatch.setattr(rest_crud, '__current_command', 'cmd2')
        monkeypatch.setattr(rest_crud, '__current_sub_command', '')

        headers1 = {}
        rest_crud.add_user_agent(headers1)
        assert 'User-Agent' in headers1

        # Second call for same command — User-Agent should NOT be overwritten via setdefault
        headers2 = {'User-Agent': 'existing-agent'}
        rest_crud.add_user_agent(headers2)
        assert headers2['User-Agent'] == 'existing-agent'


class TestSetCurrentCommand:
    """Tests for set_current_command() and set_current_sub_command() (lines 34-44)."""

    def test_set_current_sub_command(self):
        rest_crud.set_current_sub_command('list')
        # Verify via the getter path: set_current_sub_command updates __current_sub_command
        # We can't directly assert the private module var, but we confirm no exception is raised
        # and headers built via add_user_agent reflect the sub-command.
        headers = {}
        rest_crud.add_user_agent(headers)
        # No assertion on exact value — just confirming the code path runs without error.

    def test_set_current_sub_command_empty(self):
        rest_crud.set_current_sub_command('')
        # Confirm no exception


class TestBaseEndpoints:
    """Tests for base_endpoint_with_workspace() and base_endpoint() (lines 55-64)."""

    def test_base_endpoint_with_workspace_explicit(self, monkeypatch):
        if monkeypatch is None:
            return
        result = rest_crud.base_endpoint_with_workspace(ws='ws123')
        assert result == 'v3/workspaces/ws123'

    def test_base_endpoint_with_workspace_none(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        monkeypatch.setattr(rest_crud, 'get_workspace', lambda: None)
        result = rest_crud.base_endpoint_with_workspace()
        assert result == 'v2'

    def test_base_endpoint_with_workspace_from_meta(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'get_workspace', lambda: 'ws-from-meta')
        result = rest_crud.base_endpoint_with_workspace()
        assert result == 'v3/workspaces/ws-from-meta'

    def test_base_endpoint_uses_version(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        monkeypatch.setattr(user_data, 'is_version_lower_than', lambda v: True)
        assert rest_crud.base_endpoint() == 'v2'

        monkeypatch.setattr(user_data, 'is_version_lower_than', lambda v: False)
        assert rest_crud.base_endpoint() == 'v3'

    def test_get_workspace_delegates_to_user_data_meta(self, monkeypatch):
        """get_workspace() (line 60) calls user_data.get_meta('workspace id')."""
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        monkeypatch.setattr(user_data, 'get_meta', lambda key: 'ws-meta-42' if key == 'workspace id' else None)
        assert rest_crud.get_workspace() == 'ws-meta-42'

    def test_get_workspace_returns_none_when_unset(self, monkeypatch):
        if monkeypatch is None:
            return
        from neoload_cli_lib import user_data
        monkeypatch.setattr(user_data, 'get_meta', lambda key: None)
        assert rest_crud.get_workspace() is None
