import json

import pytest

import neoload_cli_lib.schema_validation as schema_validation
from neoload_cli_lib import cli_exception

_MINIMAL_SCHEMA = {
    "type": "object",
    "required": ["name"],
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "servers": {"type": "array"},
    },
}


@pytest.mark.validation
class TestResolveIncludes:

    @pytest.mark.datafiles('tests/neoload_projects/example_1')
    def test_resolves_and_merges_real_includes(self, datafiles):
        merged = schema_validation.resolve_and_merge_project(datafiles / 'default.yaml')
        assert merged['name'] == 'NeoLoad-CLI-example-2_0'
        # user_paths comes only from the included paths/geosearch_get.yaml file
        assert [up['name'] for up in merged['user_paths']] == ['ex_2_0_geosearch_get']
        # arrays declared directly in default.yaml are still present
        assert merged['servers'][0]['name'] == 'geolookup_host'
        assert merged['sla_profiles'][0]['name'] == 'geo_3rdparty_sla'

    @pytest.mark.datafiles('tests/neoload_projects/circular_includes')
    def test_detects_infinite_loop(self, datafiles):
        with pytest.raises(cli_exception.CliException) as context:
            schema_validation.resolve_and_merge_project(datafiles / 'a.yaml')
        assert 'Infinite loop' in str(context.value)

    def test_rejects_non_yaml_include(self, tmp_path):
        (tmp_path / 'notes.txt').write_text('not a project file')
        entry = tmp_path / 'entry.yaml'
        entry.write_text('name: bad-include\nincludes:\n  - notes.txt\n')

        with pytest.raises(cli_exception.CliException) as context:
            schema_validation.resolve_and_merge_project(entry)
        assert "'includes' field accepts only" in str(context.value)

    def test_missing_include_file(self, tmp_path):
        entry = tmp_path / 'entry.yaml'
        entry.write_text('name: missing-include\nincludes:\n  - does_not_exist.yaml\n')

        with pytest.raises(cli_exception.CliException) as context:
            schema_validation.resolve_and_merge_project(entry)
        assert 'As code file not found' in str(context.value)


@pytest.mark.validation
class TestMergeProjects:

    def test_concatenates_array_fields_in_order(self):
        merged = schema_validation.merge_projects([
            {'variables': [{'constant': {'name': 'a'}}]},
            {'variables': [{'constant': {'name': 'b'}}]},
        ])
        assert merged['variables'] == [{'constant': {'name': 'a'}}, {'constant': {'name': 'b'}}]

    def test_last_non_empty_name_wins(self):
        merged = schema_validation.merge_projects([
            {'name': 'included-fragment'},
            {'name': 'root-project'},
        ])
        assert merged['name'] == 'root-project'

    def test_merges_project_settings_across_files(self):
        merged = schema_validation.merge_projects([
            {'project_settings': {'dynatrace.enabled': True}},
            {'project_settings': {'qtest.enabled': True}},
        ])
        assert merged['project_settings'] == {'dynatrace.enabled': True, 'qtest.enabled': True}

    def test_preserves_unrecognized_top_level_keys(self):
        # A merge must not silently drop keys it doesn't know about - otherwise
        # invalid/unexpected content becomes invisible to schema validation
        # after the merge instead of being caught by e.g. root
        # "additionalProperties: false".
        merged = schema_validation.merge_projects([
            {'name': 'p', 'totally_unexpected_key': 'oops'},
        ])
        assert merged['totally_unexpected_key'] == 'oops'


@pytest.mark.validation
class TestValidateYamlDir:

    def test_ignores_hidden_directories(self, tmp_path):
        schema_path = tmp_path / 'schema.json'
        schema_path.write_text(json.dumps(_MINIMAL_SCHEMA))
        projects_dir = tmp_path / 'projects'
        projects_dir.mkdir()
        (projects_dir / 'project.yaml').write_text('name: my-project\n')

        # A GitHub Actions workflow (or any other tooling/CI yaml) sitting in
        # a hidden directory must never be picked up as a project file.
        workflows_dir = projects_dir / '.github' / 'workflows'
        workflows_dir.mkdir(parents=True)
        (workflows_dir / 'ci.yml').write_text('name: CI\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n')

        # Must not raise: the only real project file is valid, and .github/
        # is never descended into.
        schema_validation.validate_yaml_dir(str(projects_dir), str(schema_path))

    def test_validates_independent_root_projects_separately(self, tmp_path):
        # Keep the schema file itself outside the directory being validated -
        # otherwise the directory walk would pick it up as just another
        # ".json" file to validate as a project.
        schema_path = tmp_path / 'schema.json'
        schema_path.write_text(json.dumps(_MINIMAL_SCHEMA))
        projects_dir = tmp_path / 'projects'
        projects_dir.mkdir()

        # project-a: a root file with an included fragment - the fragment
        # must NOT be validated as if it were a complete project on its own.
        project_a = projects_dir / 'project-a'
        project_a.mkdir()
        (project_a / 'root.yaml').write_text('name: project-a\nincludes:\n  - fragment.yaml\n')
        (project_a / 'fragment.yaml').write_text('servers:\n  - name: s1\n')

        # project-b: a second, entirely independent root project.
        project_b = projects_dir / 'project-b'
        project_b.mkdir()
        (project_b / 'root.yaml').write_text('name: project-b\n')

        # Must not raise: both roots are independently valid.
        schema_validation.validate_yaml_dir(str(projects_dir), str(schema_path))

    def test_a_failing_root_does_not_block_reporting_on_the_others(self, tmp_path):
        schema_path = tmp_path / 'schema.json'
        schema_path.write_text(json.dumps(_MINIMAL_SCHEMA))
        projects_dir = tmp_path / 'projects'
        projects_dir.mkdir()

        (projects_dir / 'good.yaml').write_text('name: good-project\n')
        (projects_dir / 'bad.yaml').write_text('not_name: bad-project\n')

        with pytest.raises(ValueError, match='One or more errors'):
            schema_validation.validate_yaml_dir(str(projects_dir), str(schema_path))

    def test_no_root_found_in_empty_directory(self, tmp_path):
        empty_dir = tmp_path / 'empty'
        empty_dir.mkdir()

        with pytest.raises(cli_exception.CliException, match='No root as-code project file found'):
            schema_validation.validate_yaml_dir(str(empty_dir), str(tmp_path / 'unused-schema.json'))

    def test_mutually_circular_includes_each_report_their_own_error(self, tmp_path):
        # Neither file can be resolved as a root (each loops back into the
        # other), so both remain candidates and each surfaces its own
        # "infinite loop" error instead of one vague "no root found" message.
        (tmp_path / 'a.yaml').write_text('name: a\nincludes:\n  - b.yaml\n')
        (tmp_path / 'b.yaml').write_text('name: b\nincludes:\n  - a.yaml\n')

        with pytest.raises(ValueError, match='One or more errors'):
            schema_validation.validate_yaml_dir(str(tmp_path), str(tmp_path / 'unused-schema.json'))

    def test_nested_fragment_include_resolves_relative_to_true_root(self, tmp_path):
        # A fragment's own "includes:" is resolved relative to the true
        # root's directory (matching resolve_includes() semantics), not the
        # fragment's own directory - so it must still be recognized as a
        # fragment, and its own nested include must not become a spurious
        # root either.
        schema_path = tmp_path / 'schema.json'
        schema_path.write_text(json.dumps(_MINIMAL_SCHEMA))
        project_dir = tmp_path / 'project'
        (project_dir / 'sub').mkdir(parents=True)
        (project_dir / 'root.yaml').write_text('name: p\nincludes:\n  - sub/fragment.yaml\n')
        (project_dir / 'sub' / 'fragment.yaml').write_text('includes:\n  - sub/extra.yaml\n')
        (project_dir / 'sub' / 'extra.yaml').write_text('servers:\n  - name: s1\n')

        # Must not raise, and must only treat root.yaml as a root project.
        schema_validation.validate_yaml_dir(str(project_dir), str(schema_path))
