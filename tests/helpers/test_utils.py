import json
from datetime import datetime
from requests import Response
from neoload_cli_lib import rest_crud, user_data


def assert_success(result):
    if result.exception is not None:
        assert 'EXIT_CODE (%s): %s\n%s' % (result.exit_code, str(result.exception), result.output) == 'no error'
    assert result.exit_code == 0


def mock_api_get_with_pagination(monkeypatch, endpoint, json_result):
    __mock_api_without_data_two_args(monkeypatch, 'get_with_pagination', endpoint, json_result)


def mock_api_get(monkeypatch, endpoint, json_result):
    __mock_api_without_data(monkeypatch, 'get', endpoint, json_result)


def mock_api_get_raw(monkeypatch, endpoint, http_code, json_result):
    __mock_api_raw_without_data(monkeypatch, 'get_raw', endpoint, http_code, json_result)


def mock_api_post(monkeypatch, endpoint, json_result):
    __mock_api_with_data(monkeypatch, 'post', endpoint, json_result)


def mock_api_post_binary(monkeypatch, endpoint, http_code, json_result):
    __mock_api_raw_with_file(monkeypatch, 'post_binary_files_storage', endpoint, http_code, json_result)


def mock_api_put(monkeypatch, endpoint, json_result):
    __mock_api_with_data(monkeypatch, 'put', endpoint, json_result)


def mock_api_patch(monkeypatch, endpoint, json_result):
    __mock_api_with_data(monkeypatch, 'patch', endpoint, json_result)


def mock_api_delete_raw(monkeypatch, endpoint, http_code, json_result):
    __mock_api_raw_without_data(monkeypatch, 'delete', endpoint, http_code, json_result)


def __mock_api_without_data(monkeypatch, method, endpoint, json_result):
    if monkeypatch is not None:
        monkeypatch.setattr(rest_crud, method,
                            lambda actual_endpoint: __return_json(actual_endpoint, endpoint, json_result))
        print('Mock %s %s to return %s' % (method.upper(), endpoint, json_result))


def __mock_api_without_data_two_args(monkeypatch, method, endpoint, json_result):
    if monkeypatch is not None:
        monkeypatch.setattr(rest_crud, method,
                            lambda actual_endpoint, api_query_params: __return_json(actual_endpoint, endpoint, json_result))
        print('Mock %s %s to return %s' % (method.upper(), endpoint, json_result))


def __mock_api_raw_without_data(monkeypatch, method, endpoint, http_code, json_result):
    if monkeypatch is not None:
        monkeypatch.setattr(rest_crud, method,
                            lambda actual_endpoint: __return_response(actual_endpoint, endpoint, http_code,
                                                                      json_result))
        print('Mock %s %s to return raw response %s %s' % (method.upper(), endpoint, http_code, json_result))


def __mock_api_with_data(monkeypatch, method, endpoint, json_result):
    if monkeypatch is not None:
        monkeypatch.setattr(rest_crud, method,
                            lambda actual_endpoint, data: __return_json(actual_endpoint, endpoint, json_result))
        print('Mock %s %s to return %s' % (method.upper(), endpoint, json_result))


def __mock_api_raw_with_file(monkeypatch, method, endpoint, http_code, json_result):
    if monkeypatch is not None:
        monkeypatch.setattr(rest_crud, method,
                            lambda actual_endpoint, path, filename: __return_response(actual_endpoint, endpoint, http_code, json_result))
        print('Mock %s %s to return %s' % (method.upper(), endpoint, json_result))


def __return_json(actual_endpoint, expected_endpoint, json_result):
    if actual_endpoint == expected_endpoint:
        return json.loads(json_result)
    raise Exception('Fail ! BAD endpoint.\nActual  : %s\nExpected: %s' % (actual_endpoint, expected_endpoint))


def __return_response(actual_endpoint, expected_endpoint, http_code, json_result):
    if actual_endpoint == expected_endpoint:
        response = Response()
        response.status_code = http_code
        response._content = json_result.encode()
        return response
    raise Exception('Fail ! BAD endpoint.\nActual  : %s\nExpected: %s' % (actual_endpoint, expected_endpoint))


def generate_test_settings_name():
    return 'Test settings CLI %s' % datetime.utcnow().strftime('%b %d %H:%M:%S.%f')[:-3]


def generate_test_result_name():
    return 'Test result CLI %s' % datetime.utcnow().strftime('%b %d %H:%M:%S.%f')[:-3]


def mock_login_get_urls(monkeypatch, version='2.5.0'):
    if monkeypatch is not None:
        monkeypatch.setattr(user_data, '__compute_version_and_path',
                            lambda: user_data.get_user_data().set_url('http://front.com:8081/nlw', 'http://files.com:8082', version))


def set_line_endings_to_lf(file_path):
    """ Open the file and set all EOL character to linux LF (usefull only on windaube) """
    with open(file_path, 'r') as f:
        content = f.read()
    with open(file_path, 'w', newline='\n') as fw:
        fw.write(content)
