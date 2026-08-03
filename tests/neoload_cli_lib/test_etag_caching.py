from unittest import mock

import pytest

import neoload_cli_lib.schema_validation as schema_validation


@pytest.mark.validation
class TestEtagCaching:

    def test_sends_if_none_match_header_when_etag_cached(self):
        mock_response = mock.Mock(status_code=304)
        with mock.patch('requests.get', return_value=mock_response) as mock_get:
            content, etag, not_modified = schema_validation.get_network_schema_by_spec(
                "https://example.com/schema.json", ssl_cert='', cached_etag='"abc123"')

        assert mock_get.call_args.kwargs['headers'] == {'If-None-Match': '"abc123"'}
        assert not_modified is True
        assert content is None
        assert etag == '"abc123"'

    def test_no_if_none_match_header_without_a_cached_etag(self):
        mock_response = mock.Mock(status_code=200, text='{}')
        mock_response.headers.get.return_value = None
        with mock.patch('requests.get', return_value=mock_response) as mock_get:
            schema_validation.get_network_schema_by_spec(
                "https://example.com/schema.json", ssl_cert='', cached_etag=None)

        assert mock_get.call_args.kwargs['headers'] == {}

    def test_returns_new_content_and_etag_on_200(self):
        mock_response = mock.Mock(status_code=200, text='{"type":"object"}')
        mock_response.headers.get.return_value = '"new-etag"'
        with mock.patch('requests.get', return_value=mock_response):
            content, etag, not_modified = schema_validation.get_network_schema_by_spec(
                "https://example.com/schema.json", ssl_cert='', cached_etag=None)

        assert not_modified is False
        assert content == '{"type":"object"}'
        assert etag == '"new-etag"'

    def test_non_string_etag_header_is_ignored(self):
        # A misbehaving/mocked response whose .headers.get('ETag') doesn't
        # return a real string must not be persisted as if it were one.
        mock_response = mock.Mock(status_code=200, text='{}')
        with mock.patch('requests.get', return_value=mock_response):
            _content, etag, _not_modified = schema_validation.get_network_schema_by_spec(
                "https://example.com/schema.json", ssl_cert='', cached_etag=None)

        assert etag is None

    def test_network_failure_keeps_cached_etag_and_returns_no_content(self):
        with mock.patch('requests.get', side_effect=Exception("boom")):
            content, etag, not_modified = schema_validation.get_network_schema_by_spec(
                "https://example.com/schema.json", ssl_cert='', cached_etag='"abc"')

        assert content is None
        assert not_modified is False
        assert etag == '"abc"'
