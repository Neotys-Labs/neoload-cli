---
phase: 02-core-resources
verified: 2026-04-09T12:00:00Z
status: passed
score: 38/38 must-haves verified
overrides_applied: 0
---

# Phase 2: Core Resources Verification Report

**Phase Goal:** Implement the 5 core v4 resource commands (v4-tests, v4-results, v4-test-executions, v4-workspaces, v4-zones) each with full CRUD subcommands and comprehensive unit tests.
**Verified:** 2026-04-09T12:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | neoload v4-tests ls returns a JSON list of tests for the current workspace | VERIFIED | v4_tests.py:35 calls `v4_client.v4_list('tests')`; test_ls passes |
| 2 | neoload v4-tests create --name X posts a new test with workspaceId injected | VERIFIED | v4_tests.py:39 calls `v4_client.v4_create('tests', data=body)`; test_create_with_name passes |
| 3 | neoload v4-tests get `<id>` returns single test JSON | VERIFIED | v4_tests.py:44 calls `v4_client.v4_get('tests', id)`; test_get passes |
| 4 | neoload v4-tests patch `<id>` --name X patches the test | VERIFIED | v4_tests.py:50 calls `v4_client.v4_update('tests', id, data=body)`; test_patch passes |
| 5 | neoload v4-tests delete `<id>` deletes the test | VERIFIED | v4_tests.py:63 calls `v4_client.v4_delete('tests', id)`; test_delete passes |
| 6 | neoload v4-tests delete --delete-results passes ?deleteResults=true query param | VERIFIED | v4_tests.py:56 appends `?deleteResults=true`; test_delete_with_results_flag passes |
| 7 | neoload v4-tests scenario-get `<testId>` `<scenarioName>` returns the scenario | VERIFIED | v4_tests.py:74 calls `v4_client.v4_get('tests', id, 'scenarios', scenario_name)`; test_scenario_get passes |
| 8 | neoload v4-tests scenario-update `<testId>` `<scenarioName>` --file updates the scenario | VERIFIED | v4_tests.py:84 calls `v4_client.v4_replace('tests', id, 'scenarios', scenario_name, data=body)`; test_scenario_update passes |
| 9 | neoload v4-results ls returns a JSON list of results for the current workspace | VERIFIED | v4_results.py:37 calls `v4_client.v4_list('results')`; test_ls passes |
| 10 | neoload v4-results get `<id>` returns single result JSON | VERIFIED | v4_results.py:53 calls `v4_client.v4_get('results', id)`; test_get passes |
| 11 | neoload v4-results patch `<id>` --name X patches the result | VERIFIED | v4_results.py:56 calls `v4_client.v4_update('results', id, data=body)`; test_patch passes |
| 12 | neoload v4-results delete `<id>` deletes the result | VERIFIED | v4_results.py:58 calls `v4_client.v4_delete('results', id)`; test_delete_returns_none passes |
| 13 | neoload v4-results contexts `<id>` returns result contexts | VERIFIED | v4_results.py:64 dispatches `v4_client.v4_get('results', id, 'contexts')`; test_contexts passes |
| 14 | neoload v4-results elements `<id>` returns result elements | VERIFIED | v4_results.py:64 dispatches `v4_client.v4_get('results', id, 'elements')`; test_elements passes |
| 15 | neoload v4-results monitors `<id>` returns result monitors | VERIFIED | v4_results.py:64 dispatches `v4_client.v4_get('results', id, 'monitors')`; test_monitors passes |
| 16 | neoload v4-results statistics `<id>` returns result statistics | VERIFIED | v4_results.py:64 dispatches `v4_client.v4_get('results', id, 'statistics')`; test_statistics passes |
| 17 | neoload v4-results timeseries `<id>` returns result timeseries | VERIFIED | v4_results.py:64 dispatches `v4_client.v4_get('results', id, 'timeseries')`; test_timeseries passes |
| 18 | neoload v4-results search-criteria returns search criteria for the workspace | VERIFIED | v4_results.py:42-45 calls `rest_crud.get(v4_endpoint(...), v4_workspace_params())`; test_search_criteria passes |
| 19 | neoload v4-test-executions create --test-id X posts to /v4/test-executions and returns execution JSON | VERIFIED | v4_test_executions.py:51 calls `rest_crud.post(v4_endpoint('test-executions'), body)`; test_create_no_wait passes |
| 20 | neoload v4-test-executions create --test-id X --wait polls until terminal status and exits 0 on PASSED | VERIFIED | v4_test_executions.py:127-139 `_wait_for_completion`; test_create_with_wait_passed exits 0 |
| 21 | neoload v4-test-executions create --test-id X --wait exits 1 on FAILED or CANCELLED | VERIFIED | v4_test_executions.py:137 `sys.exit(1)` on FAIL_EXIT_STEPS; test_create_with_wait_failed and test_create_with_wait_cancelled both assert exit_code==1 |
| 22 | neoload v4-test-executions create --scenario S --zone-type Z passes scenarioName and zoneType in request body | VERIFIED | v4_test_executions.py:113-115 maps --scenario -> scenarioName, --zone-type -> zoneType; test_create_with_scenario_flag and test_create_with_zone_type_flag pass |
| 23 | neoload v4-test-executions get `<id>` returns execution JSON | VERIFIED | v4_test_executions.py:64 calls `v4_client.v4_get('test-executions', id)`; test_get passes |
| 24 | neoload v4-test-executions cancel `<id>` sends DELETE and prints confirmation | VERIFIED | v4_test_executions.py:70 calls `rest_crud.delete(v4_endpoint('test-executions', id))`; test_cancel passes |
| 25 | neoload v4-test-executions force-cancel `<id>` sends DELETE to /forced endpoint | VERIFIED | v4_test_executions.py:81 calls `rest_crud.delete(v4_endpoint('test-executions', id, 'forced'))`; test_force_cancel asserts 'forced' in endpoint |
| 26 | neoload v4-test-executions logs `<resultId>` polls log pages and prints log lines | VERIFIED | v4_test_executions.py:142-162 `_poll_logs` polls /v4/results/{id}/logs; test_logs and test_logs_endpoint_uses_results_path pass |
| 27 | neoload v4-workspaces ls returns a JSON list of workspaces without requiring workspaceId | VERIFIED | v4_workspaces.py:97-113 `_workspace_list` uses `rest_crud.get` without workspaceId; test_ls passes |
| 28 | neoload v4-workspaces create --name X creates a workspace | VERIFIED | v4_workspaces.py:41 calls `rest_crud.post(v4_endpoint('workspaces'), body)`; test_create passes |
| 29 | neoload v4-workspaces get `<id>` returns workspace JSON | VERIFIED | v4_workspaces.py:49 calls `v4_client.v4_get('workspaces', id)`; test_get passes |
| 30 | neoload v4-workspaces patch `<id>` --name X patches the workspace | VERIFIED | v4_workspaces.py:54 calls `v4_client.v4_update('workspaces', id, data=body)`; test_patch passes |
| 31 | neoload v4-workspaces delete `<id>` deletes the workspace | VERIFIED | v4_workspaces.py:58 calls `v4_client.v4_delete('workspaces', id)`; test_delete passes |
| 32 | neoload v4-workspaces members-ls `<id>` returns workspace members | VERIFIED | v4_workspaces.py:66 calls `v4_client.v4_get('workspaces', id, 'members')`; test_members_ls passes |
| 33 | neoload v4-workspaces members-add `<id>` --file adds a member using rest_crud.post directly | VERIFIED | v4_workspaces.py:76-77 calls `rest_crud.post(v4_endpoint('workspaces', id, 'members'), body)`; test_members_add passes with no workspaceId in body |
| 34 | neoload v4-workspaces members-remove `<id>` --login X deletes member with login encoded in URL | VERIFIED | v4_workspaces.py:84-85 uses `urllib.parse.urlencode({'login': login})`; test_members_remove_url_encodes_special_chars passes |
| 35 | neoload v4-workspaces subscription `<id>` returns workspace subscription info | VERIFIED | v4_workspaces.py:93 calls `v4_client.v4_get('workspaces', id, 'subscription')`; test_subscription passes |
| 36 | neoload v4-zones ls returns a JSON list of zones without requiring workspaceId | VERIFIED | v4_zones.py:63-79 `_zone_list` uses `rest_crud.get` without workspaceId; test_ls passes |
| 37 | neoload v4-zones ls --type STATIC filters zones by type | VERIFIED | v4_zones.py:31-33 passes `params['type']` from --type flag; test_ls_with_type asserts param is set |
| 38 | neoload v4-zones create --name X --type STATIC creates a zone | VERIFIED | v4_zones.py:38 calls `rest_crud.post(v4_endpoint('zones'), body)`; test_create passes with no workspaceId |
| 39 | neoload v4-zones get `<id>` returns zone JSON | VERIFIED | v4_zones.py:46 calls `v4_client.v4_get('zones', zone_id)`; test_get passes |
| 40 | neoload v4-zones patch `<id>` --file body.json replaces the zone via PUT | VERIFIED | v4_zones.py:51 calls `v4_client.v4_replace('zones', zone_id, data=body)`; test_patch_uses_replace asserts v4_replace called |
| 41 | neoload v4-zones delete `<id>` deletes the zone | VERIFIED | v4_zones.py:55 calls `v4_client.v4_delete('zones', zone_id)`; test_delete passes |

**Score:** 38/38 truths verified (the plans define 38 total truths across 5 plans)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `neoload/commands/v4_tests.py` | v4-tests CLI with 7 subcommands | VERIFIED | 102 lines, exports `cli`, all 7 subcommands dispatched |
| `tests/commands/test_v4_tests.py` | Unit tests for all v4-tests subcommands | VERIFIED | 20 tests, all pass, `class TestV4Tests` present |
| `neoload/commands/v4_results.py` | v4-results CLI with 10 subcommands | VERIFIED | 80 lines, exports `cli`, all 10 subcommands dispatched |
| `tests/commands/test_v4_results.py` | Unit tests for all v4-results subcommands | VERIFIED | 16 tests, all pass, `class TestV4Results` present |
| `neoload/commands/v4_test_executions.py` | v4-test-executions CLI with 5 subcommands, --wait, logs polling | VERIFIED | 163 lines, exports `cli`, all 5 subcommands, `_wait_for_completion`, `_poll_logs` present |
| `tests/commands/test_v4_test_executions.py` | Unit tests for v4-test-executions | VERIFIED | 15 tests, all pass, `class TestV4TestExecutions` present |
| `neoload/commands/v4_workspaces.py` | v4-workspaces CLI with 9 subcommands | VERIFIED | 127 lines, exports `cli`, all 9 subcommands dispatched |
| `tests/commands/test_v4_workspaces.py` | Unit tests for all v4-workspaces subcommands | VERIFIED | 16 tests, all pass, `class TestV4Workspaces` present |
| `neoload/commands/v4_zones.py` | v4-zones CLI with 5 subcommands | VERIFIED | 98 lines, exports `cli`, all 5 subcommands dispatched |
| `tests/commands/test_v4_zones.py` | Unit tests for all v4-zones subcommands | VERIFIED | 14 tests, all pass, `class TestV4Zones` present |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| v4_tests.py | v4_client.py | v4_list, v4_get, v4_create, v4_update, v4_delete, v4_replace | WIRED | 7 v4_client calls confirmed in file |
| v4_tests.py | rest_crud | rest_crud.delete for --delete-results | WIRED | Line 57: `rest_crud.delete(endpoint)` with ?deleteResults=true |
| v4_tests.py | tools.py | print_json for all output | WIRED | 8 calls to tools.print_json |
| v4_results.py | v4_client.py | v4_list, v4_get, v4_update, v4_delete | WIRED | 5 v4_client calls confirmed |
| v4_results.py | v4_endpoints.py | v4_endpoint and v4_workspace_params for search-criteria | WIRED | Lines 43-44 call both functions |
| v4_test_executions.py | rest_crud.py | rest_crud.post for create, rest_crud.get for logs, rest_crud.delete for cancel | WIRED | All 3 rest_crud operations present |
| v4_test_executions.py | v4_client.py | v4_get for polling and get subcommand | WIRED | Lines 64 and 130 |
| v4_workspaces.py | rest_crud.py | rest_crud.get for ls, rest_crud.post for create/members-add, rest_crud.delete for members-remove | WIRED | All present, confirmed in file |
| v4_workspaces.py | v4_client.py | v4_get, v4_update, v4_delete | WIRED | 5 v4_client calls confirmed |
| v4_zones.py | rest_crud.py | rest_crud.get for ls pagination, rest_crud.post for create | WIRED | Both present in file |
| v4_zones.py | v4_client.py | v4_get, v4_replace, v4_delete | WIRED | 3 v4_client calls confirmed (no v4_update used — correct: patch uses v4_replace) |

### Data-Flow Trace (Level 4)

Not applicable — these are CLI command modules that call external APIs via monkeypatched dependencies in tests. Data flows to stdout via `tools.print_json`. The test suite verifies that data returned from mocked API calls reaches stdout output correctly.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All v4_tests tests pass | `python3 -m pytest tests/commands/test_v4_tests.py -q` | 20 passed | PASS |
| All v4_results tests pass | `python3 -m pytest tests/commands/test_v4_results.py -q` | 16 passed | PASS |
| All v4_test_executions tests pass | `python3 -m pytest tests/commands/test_v4_test_executions.py -q` | 15 passed | PASS |
| All v4_workspaces tests pass | `python3 -m pytest tests/commands/test_v4_workspaces.py -q` | 16 passed | PASS |
| All v4_zones tests pass | `python3 -m pytest tests/commands/test_v4_zones.py -q` | 14 passed | PASS |
| Full phase test run | `python3 -m pytest tests/commands/test_v4_*.py -q` | 81 passed in 0.18s | PASS |
| All 5 command files importable | python3 -c import check | All 5 import ok | PASS |

### Requirements Coverage

No explicit requirements IDs were referenced in the plan frontmatter (`requirements: []` in all 5 plans). The phase requirements are expressed as plan must-haves and ROADMAP success criteria, all of which are verified above.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| v4_zones.py | Missing `rest_crud.set_current_command()` and `rest_crud.set_current_sub_command()` calls | Info | Inconsistent with the pattern established in v4_tests, v4_results, v4_test_executions, v4_workspaces. The calls set internal tracking state used by rest_crud for error context. Does not block any plan acceptance criterion and does not prevent goal achievement. |

No stubs, no TODO/FIXME/placeholder markers, no hardcoded empty returns, no Resolver usage, no @click.group usage found in any of the 5 command files.

**Additive-only constraint:** Verified. All 10 new files (5 command + 5 test) are additions. No existing v2/v3 command or library files were modified.

**CLI registration:** Verified. The `__main__.py` dynamic loader auto-discovers any `*.py` in `neoload/commands/`, converting underscores to hyphens. All 5 new files are auto-registered as `v4-tests`, `v4-results`, `v4-test-executions`, `v4-workspaces`, `v4-zones`.

### Human Verification Required

None. All must-haves are programmatically verifiable and verified via unit tests and code inspection.

### Gaps Summary

No gaps. All 38 observable truths verified, all 10 artifacts present and substantive, all key links wired, all 81 unit tests pass. The single anti-pattern noted (missing `set_current_command` in v4_zones.py) is a minor inconsistency that is explicitly outside the plan's acceptance criteria and does not affect goal achievement.

---

_Verified: 2026-04-09T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
