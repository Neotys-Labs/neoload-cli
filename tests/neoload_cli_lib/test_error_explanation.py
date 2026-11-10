import jsonschema

from neoload_cli_lib import schema_validation

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


def explain(project):
    validator = jsonschema.Draft201909Validator(SCHEMA)
    return schema_validation.explain_validation_errors(validator, project)


def project_with(request):
    return {"user_paths": [{"name": "Path", "actions": {"steps": [
        {"transaction": {"name": "Login", "steps": [{"request": request}]}}]}}]}


def test_unexpected_key_is_reported_on_the_request_not_on_the_enclosing_oneof():
    errors = explain(project_with({"url": "/a", "name": "x"}))
    assert errors[0] == '1 error(s)'
    assert len(errors) == 2
    assert "'name' was unexpected" in errors[1]
    assert 'at: user_paths[0].actions.steps[0].transaction.steps[0].request' in errors[1]
    assert "transaction 'Login' > request '/a'" in errors[1]


def test_every_real_mistake_is_listed_with_its_own_path():
    errors = explain(project_with({"url": "foo", "follow_redirects": "yes"}))
    assert errors[0] == '2 error(s)'
    paths = [line for e in errors[1:] for line in e.split('\n') if 'at:' in line]
    assert any(p.endswith('request.url') for p in paths)
    assert any(p.endswith('request.follow_redirects') for p in paths)


def test_invalid_value_is_not_also_reported_as_unevaluated_property():
    errors = explain(project_with({"url": "/a", "follow_redirects": "yes"}))
    assert errors[0] == '1 error(s)'
    assert "is not of type 'boolean'" in errors[1]
    assert 'unexpected' not in ' '.join(errors)


def test_unknown_step_lists_the_keys_found_instead_of_dumping_the_subtree():
    project = {"user_paths": [{"name": "Path", "actions": {"steps": [{"requst": {"url": "/a" * 200}}]}}]}
    errors = explain(project)
    assert errors[0] == '1 error(s)'
    assert 'found the keys: requst' in errors[1]
    assert '/a/a/a' not in errors[1]


def test_offending_value_is_truncated():
    errors = explain(project_with({"url": "/a", "extra": "x" * 1000}))
    assert len(errors[1]) < 600


def test_valid_project_gives_no_errors():
    assert explain(project_with({"url": "/a"})) == ['0 error(s)']


def test_same_mistake_on_many_steps_is_one_entry_with_all_the_places():
    steps = [{"request": {"url": "/a%d" % i, "name": "x"}} for i in range(10)]
    project = {"user_paths": [{"name": "Path", "actions": {"steps": [{"transaction": {"name": "T", "steps": steps}}]}}]}
    errors = explain(project)
    assert errors[0] == '1 error(s) (10 places)'
    assert len(errors) == 2
    assert 'and 6 more' in errors[1]
