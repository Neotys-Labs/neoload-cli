import json
from datetime import datetime

from neoload_cli_lib import rest_crud


def assert_success(result):
    if result.exception is not None:
        assert 'EXIT_CODE (%s): %s\n%s' % (result.exit_code, str(result.exception), result.output) == 'no error'
    assert result.exit_code == 0


def mock_api_get(monkeypatch, endpoint, json_result):
    __mock_api_without_data(monkeypatch, 'get', endpoint, json_result)


def mock_api_post(monkeypatch, endpoint, json_result):
    __mock_api_with_data(monkeypatch, 'post', endpoint, json_result)


def mock_api_post_binary(monkeypatch, endpoint, json_result):
    __mock_api_with_data(monkeypatch, 'post', endpoint, json_result)


def mock_api_put(monkeypatch, endpoint, json_result):
    __mock_api_with_data(monkeypatch, 'put', endpoint, json_result)


def mock_api_patch(monkeypatch, endpoint, json_result):
    __mock_api_with_data(monkeypatch, 'patch', endpoint, json_result)


def mock_api_delete(monkeypatch, endpoint, json_result):
    __mock_api_without_data(monkeypatch, 'delete', endpoint, json_result)


def __mock_api_without_data(monkeypatch, method, endpoint, json_result):
    monkeypatch.setattr(rest_crud, method,
                        lambda actual_endpoint: __return_json(actual_endpoint, endpoint, json_result))
    print('Mock %s %s to return %s' % (method.upper(), endpoint, json_result))


def __mock_api_with_data(monkeypatch, method, endpoint, json_result):
    monkeypatch.setattr(rest_crud, method,
                        lambda actual_endpoint, data: __return_json(actual_endpoint, endpoint, json_result))
    print('Mock %s %s to return %s' % (method.upper(), endpoint, json_result))


def __return_json(actual_endpoint, expected_endpoint, json_result):
    if actual_endpoint == expected_endpoint:
        return json.loads(json_result)
    raise Exception('Fail ! BAD endpoint.\nActual  : %s\nExpected: %s' % (actual_endpoint, expected_endpoint))


def generate_test_settings_name():
    return 'Test settings CLI %s' % datetime.utcnow().strftime('%b %d %H:%M:%S.%f')[:-3]


def generate_test_result_name():
    return 'Test result CLI %s' % datetime.utcnow().strftime('%b %d %H:%M:%S.%f')[:-3]
