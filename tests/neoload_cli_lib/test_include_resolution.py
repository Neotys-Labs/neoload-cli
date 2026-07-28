import pytest

import neoload_cli_lib.schema_validation as schema_validation
from neoload_cli_lib import cli_exception


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
