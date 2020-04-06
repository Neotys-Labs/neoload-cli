import json
from neoload_cli_lib import rest_crud


def assert_success(result_use):
    if result_use.exception is not None:
        assert str(result_use.exception) == ''
    assert result_use.exit_code == 0


def mock_api(monkeypatch, method, endpoint, json_result):
    monkeypatch.setattr(rest_crud, method,
                        lambda actual_endpoint: __return_json(actual_endpoint, endpoint, json_result))
    print('Mock %s %s to return %s' % (method.upper(), endpoint, json_result))


def __return_json(actual_endpoint, expected_endpoint, json_result):
    if actual_endpoint == expected_endpoint:
        return json.loads(json_result)
    raise Exception('Fail ! BAD endpoint.\nActual  : %s\nExpected: %s' % (actual_endpoint, expected_endpoint))
