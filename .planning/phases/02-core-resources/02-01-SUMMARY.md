---
phase: 02-core-resources
plan: "01"
subsystem: v4-tests-command
tags: [v4, click, tests-crud, scenarios]
dependency_graph:
  requires:
    - neoload/neoload_cli_lib/v4/v4_client.py
    - neoload/neoload_cli_lib/v4/v4_endpoints.py
    - neoload/neoload_cli_lib/rest_crud.py
    - neoload/neoload_cli_lib/tools.py
    - neoload/neoload_cli_lib/cli_exception.py
  provides:
    - neoload/commands/v4_tests.py
    - tests/commands/test_v4_tests.py
  affects: []
tech_stack:
  added: []
  patterns:
    - click.Choice single-command dispatch pattern (not click.group)
    - v4_client wrappers for all HTTP operations
    - --file + named flags override pattern (D-02)
    - raw rest_crud.delete for custom query params (?deleteResults=true)
key_files:
  created:
    - neoload/commands/v4_tests.py
    - tests/commands/test_v4_tests.py
  modified: []
decisions:
  - "Used rest_crud.delete directly for --delete-results to append ?deleteResults=true query param since v4_client.v4_delete does not support custom query params"
  - "Named flags (--name, --description, --scenario) override file values per D-02"
  - "scenario-update uses v4_replace (PUT) per plan spec, scenario-get uses v4_get"
metrics:
  duration: "2m 29s"
  completed_date: "2026-04-09"
  tasks_completed: 2
  files_created: 2
---

# Phase 02 Plan 01: v4-tests Command Summary

**One-liner:** v4-tests CLI command with 7 subcommands (ls, create, get, patch, delete, scenario-get, scenario-update) using Click Choice dispatch, v4_client wrappers, and --delete-results ?deleteResults=true query param support.

## What Was Built

### `neoload/commands/v4_tests.py`

A new v4 command file implementing the `neoload v4-tests` CLI command with all 7 subcommands:

- **ls** — auto-paginating list via `v4_client.v4_list('tests')`
- **create** — POST with workspace injection via `v4_client.v4_create('tests', data=body)`; accepts `--file` JSON and/or named flags (`--name`, `--description`, `--scenario`)
- **get** — single resource fetch via `v4_client.v4_get('tests', id)`
- **patch** — PATCH via `v4_client.v4_update('tests', id, data=body)`; same `--file` + named flags pattern
- **delete** — DELETE via `v4_client.v4_delete('tests', id)`; `--delete-results` flag uses `rest_crud.delete` directly with `?deleteResults=true` appended
- **scenario-get** — nested GET via `v4_client.v4_get('tests', id, 'scenarios', scenario_name)`
- **scenario-update** — nested PUT via `v4_client.v4_replace('tests', id, 'scenarios', scenario_name, data=body)`

All output uses `tools.print_json`. All errors use `CliException`. No `Resolver`, no name-based lookup (D-07).

### `tests/commands/test_v4_tests.py`

20 unit tests covering:
- All 7 subcommands (happy path)
- Missing required argument error cases (get/patch without id, scenario-get without scenario_name, scenario-update without --file)
- `--delete-results` flag verifying `?deleteResults=true` in endpoint
- `--file` + named flag override behavior (D-02)
- Invalid JSON file input raises CliException
- Missing command prints help message

## Decisions Made

1. **rest_crud.delete for --delete-results**: `v4_client.v4_delete` doesn't support custom query parameters. Using `rest_crud.delete` directly allows appending `?deleteResults=true` to the endpoint URL.
2. **Named flags override file values**: Per D-02, `_build_body` loads file first, then applies named flags — this ensures flags take precedence.
3. **v4_replace for scenario-update**: The plan spec calls for PUT semantics for scenario updates; `v4_replace` maps to `rest_crud.put`.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all subcommands are fully wired to v4_client.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced beyond what the plan's threat model covers (T-02-01: JSON file input validated via json.load; T-02-02: ID path injection; T-02-03: API error responses).

## Self-Check: PASSED

- FOUND: neoload/commands/v4_tests.py
- FOUND: tests/commands/test_v4_tests.py
- FOUND commit: c7d3507 (feat(02-01): implement v4-tests command)
- FOUND commit: 184d8f8 (test(02-01): add unit tests)
- All 20 pytest tests pass
