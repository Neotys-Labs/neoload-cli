import json

import pytest

import neoload_cli_lib.schema_validation as schema_validation
from neoload_cli_lib import cli_exception

# A minimal schema using "unevaluatedProperties", a Draft 2019-09+ keyword that
# Draft-07 validators silently ignore (unknown keywords are not an error, just
# a no-op). Used to prove which draft is actually being applied.
_BASE_SCHEMA = {
    "type": "object",
    "required": ["name"],
    "allOf": [
        {"properties": {"name": {"type": "string"}}}
    ],
    "unevaluatedProperties": False,
}


def _schema_with(schema_keyword):
    schema = dict(_BASE_SCHEMA)
    if schema_keyword is not None:
        schema = {"$schema": schema_keyword, **schema}
    return schema


@pytest.mark.validation
class TestValidatorSelection:

    def _validate(self, tmp_path, schema_keyword, project):
        schema_path = tmp_path / 'schema.json'
        schema_path.write_text(json.dumps(_schema_with(schema_keyword)))
        schema_validation.validate_project_object(project, str(schema_path), check_schema=True)

    def test_draft_2019_09_enforces_unevaluated_properties(self, tmp_path):
        with pytest.raises(cli_exception.CliException):
            self._validate(tmp_path, "https://json-schema.org/draft/2019-09/schema",
                            {"name": "ok", "unexpected": "nope"})

    def test_draft_7_ignores_unevaluated_properties(self, tmp_path):
        # Draft-07 doesn't know "unevaluatedProperties" - it's just an
        # unrecognized keyword, so an extra property is NOT rejected.
        self._validate(tmp_path, "http://json-schema.org/draft-07/schema#",
                        {"name": "ok", "unexpected": "fine-on-draft-07"})

    def test_missing_schema_field_falls_back_to_draft_7(self, tmp_path):
        # No "$schema" declared at all - falls back to Draft7Validator, same
        # behaviour as the draft-07 case above.
        self._validate(tmp_path, None, {"name": "ok", "unexpected": "fine-by-default"})
