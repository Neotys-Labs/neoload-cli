import jsonschema

from neoload_cli_lib import schema_error_report

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2019-09/schema",
    "type": "object",
    "properties": {
        "user_paths": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "actions": {"$ref": "#/$defs/container"}},
            },
        }
    },
    "$defs": {
        "container": {
            "type": "object",
            "properties": {"steps": {"type": "array", "items": {"oneOf": [
                {"required": ["transaction"], "properties": {"transaction": {"$ref": "#/$defs/transaction"}}},
                {"required": ["request"], "properties": {"request": {"$ref": "#/$defs/request"}}},
            ]}}},
        },
        "transaction": {
            "type": "object", "required": ["steps"], "unevaluatedProperties": False,
            "properties": {"name": {"type": "string"}, "steps": {"type": "array", "items": {"oneOf": [
                {"required": ["request"], "properties": {"request": {"$ref": "#/$defs/request"}}},
            ]}}},
        },
        "request": {
            "type": "object", "required": ["url"], "unevaluatedProperties": False,
            "properties": {"url": {"type": "string", "pattern": "^/"}, "follow_redirects": {"type": "boolean"}},
        },
    },
}


def report(project):
    errors = jsonschema.Draft201909Validator(SCHEMA).iter_errors(project)
    return schema_error_report.format_errors(errors, project)


def project_with(request):
    return {"user_paths": [{"name": "Path", "actions": {"steps": [
        {"transaction": {"name": "Login", "steps": [{"request": request}]}}]}}]}


def project_with_requests(*requests, transaction_name="T"):
    steps = [{"request": request} for request in requests]
    return {"user_paths": [{"name": "Path", "actions": {"steps": [
        {"transaction": {"name": transaction_name, "steps": steps}}]}}]}


def test_unexpected_key_is_reported_on_the_request_not_on_the_enclosing_oneof():
    text = report(project_with({"url": "/a", "name": "x"}))
    assert text.splitlines()[0] == '1 error(s)'
    assert "'name' was unexpected" in text
    assert 'at: user_paths[0].actions.steps[0].transaction.steps[0].request' in text
    assert "in: user_path 'Path' > transaction 'Login' > request '/a'" in text


def test_every_real_mistake_is_listed_with_its_own_path():
    text = report(project_with({"url": "foo", "follow_redirects": "yes"}))
    assert text.splitlines()[0] == '2 error(s)'
    assert 'request.url' in text
    assert 'request.follow_redirects' in text


def test_invalid_value_is_not_also_reported_as_unexpected_key():
    text = report(project_with({"url": "/a", "follow_redirects": "yes"}))
    assert text.splitlines()[0] == '1 error(s)'
    assert "is not of type 'boolean'" in text
    assert 'unexpected' not in text


def test_unknown_step_lists_the_keys_found_instead_of_dumping_the_subtree():
    project = {"user_paths": [{"name": "Path", "actions": {"steps": [{"requst": {"url": "/a" * 200}}]}}]}
    text = report(project)
    assert text.splitlines()[0] == '1 error(s)'
    assert 'found the keys: requst' in text
    assert '/a/a/a' not in text


def test_offending_value_is_truncated():
    text = report(project_with({"url": "/a", "extra": "x" * 1000}))
    assert len(text) < 600


def test_valid_project_has_no_errors():
    assert report(project_with({"url": "/a"})) == '0 error(s)'


def test_same_mistake_on_many_steps_is_one_entry_with_all_the_places():
    text = report(project_with_requests(*[{"url": "/a%d" % i, "name": "x"} for i in range(10)]))
    assert text.splitlines()[0] == '1 error(s) (10 places)'
    assert 'and 6 more' in text


def test_same_mistake_under_different_parents_is_merged_and_paths_are_abbreviated():
    project = {"user_paths": [{"name": "Path", "actions": {"steps": [
        {"transaction": {"name": "A", "steps": [{"request": {"url": "/a", "name": "x"}}]}},
        {"transaction": {"name": "B", "steps": [{"request": {"url": "/b", "name": "y"}}]}}]}}]}
    text = report(project)
    assert text.splitlines()[0] == '1 error(s) (2 places)'
    assert 'also at: ...steps[1].transaction.steps[0].request' in text


def test_elide_shared_prefix_keeps_the_last_element():
    assert schema_error_report.elide_shared_prefix('a.b.c.d', 'a.b.x.y') == '...c.d'
    assert schema_error_report.elide_shared_prefix('x.y', 'a.b') == 'x.y'
    assert schema_error_report.elide_shared_prefix('a.b', 'a.b') == '...b'


def test_format_path():
    assert schema_error_report.format_path(('user_paths', 0, 'actions')) == 'user_paths[0].actions'
    assert schema_error_report.format_path(()) == '(root)'


def test_places_are_listed_in_document_order():
    text = report(project_with_requests(*[{"url": "/a%d" % i, "name": "x"} for i in range(12)]))
    assert 'also at: ...steps[1].request, ...steps[2].request, ...steps[3].request and 8 more' in text
