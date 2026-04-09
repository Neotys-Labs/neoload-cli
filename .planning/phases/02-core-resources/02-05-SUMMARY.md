---
phase: 02-core-resources
plan: 05
subsystem: v4-zones
tags: [cli, zones, v4, crud]
dependency_graph:
  requires:
    - neoload/neoload_cli_lib/v4/v4_client.py
    - neoload/neoload_cli_lib/v4/v4_endpoints.py
    - neoload/neoload_cli_lib/rest_crud.py
  provides:
    - neoload/commands/v4_zones.py
  affects: []
tech_stack:
  added: []
  patterns:
    - click.Choice single-command dispatch with 5 subcommands
    - Manual pageNumber/pageSize pagination (zones not workspace-scoped)
    - rest_crud.post for create (no workspaceId injection)
    - v4_client.v4_replace (PUT) for patch subcommand
key_files:
  created:
    - neoload/commands/v4_zones.py
    - tests/commands/test_v4_zones.py
  modified: []
decisions:
  - Zones are not workspace-scoped: ls/create use rest_crud directly, not v4_list/v4_create
  - patch subcommand uses v4_replace (PUT) not v4_update (PATCH) per API spec (PUT only for single zone update)
  - Zone IDs (5-6 char alphanumeric like aBcDe) are not validated with tools.is_id() (UUID validator)
metrics:
  duration: ~8 minutes
  completed: 2026-04-09T11:34:22Z
  tasks_completed: 2
  files_created: 2
---

# Phase 02 Plan 05: v4-zones Command Summary

## One-liner

v4-zones CLI command with ls/create/get/patch/delete using manual pagination and REST-direct create (non-workspace-scoped)

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create v4_zones.py command file | 0d00060 | neoload/commands/v4_zones.py |
| 2 | Create test_v4_zones.py unit tests | 020c1af | tests/commands/test_v4_zones.py |

## What Was Built

### v4_zones.py

A single `@click.command()` with `click.Choice` dispatch for 5 subcommands:

- **ls** — paginated GET /v4/zones via manual `_zone_list()` helper; optional `--type STATIC|DYNAMIC|CLOUD` filter passed as query param; no workspaceId injection
- **create** — POST /v4/zones via `rest_crud.post()` directly (not `v4_create`, which injects workspaceId)
- **get** — GET /v4/zones/{id} via `v4_client.v4_get()`
- **patch** — PUT /v4/zones/{id} via `v4_client.v4_replace()` (full replace per API spec, despite "patch" subcommand name)
- **delete** — DELETE /v4/zones/{id} via `v4_client.v4_delete()`; handles both None (202/empty) and dict (body) responses

Two helpers:
- `_zone_list(extra_params)` — manual pageNumber/pageSize pagination loop
- `_build_body(input_file, name, description, zone_type)` — builds request body from `--file` or named flags; flags override file values

### test_v4_zones.py

14 unit tests in `TestV4Zones` class (`@pytest.mark.usefixtures("neoload_login")`):

- `test_ls` — zone listing returns and prints zone id
- `test_ls_with_type` — `--type STATIC` passes type param to rest_crud.get
- `test_ls_type_dynamic` — `--type DYNAMIC` passes correct param
- `test_create` — rest_crud.post called with correct body
- `test_create_does_not_inject_workspace` — workspaceId absent from body
- `test_get` — v4_client.v4_get called, output contains id
- `test_patch_uses_replace` — v4_client.v4_replace called (not v4_update)
- `test_delete` — None response prints "Zone deleted."
- `test_delete_with_response_body` — dict response prints JSON
- `test_missing_command` — empty invocation prints help hint
- `test_get_missing_id` — get without zone_id exits non-zero
- `test_patch_missing_id` — patch without zone_id exits non-zero
- `test_delete_missing_id` — delete without zone_id exits non-zero
- `test_ls_pagination` — multi-page pagination fetches all items across 2 pages

## Deviations from Plan

None — plan executed exactly as written.

## Threat Model Coverage

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-02-15 | `--file` parsed with `json.load()`; malformed raises CliException | Implemented |
| T-02-16 | Zone IDs passed through v4_endpoint path join; API validates server-side | Accepted (no client validation) |
| T-02-17 | `--type` constrained by `click.Choice(['STATIC', 'DYNAMIC', 'CLOUD'])` | Implemented |

## Known Stubs

None — all subcommands are fully wired to v4 client / rest_crud calls.

## Threat Flags

None — no new network endpoints or auth paths beyond those planned.

## Self-Check: PASSED

- [x] neoload/commands/v4_zones.py exists
- [x] tests/commands/test_v4_zones.py exists
- [x] Commit 0d00060 exists (feat: v4_zones.py command file)
- [x] Commit 020c1af exists (test: unit tests for v4-zones)
- [x] 14/14 tests pass
- [x] No forbidden patterns (v4_list, v4_create, v4_update) in v4_zones.py
- [x] v4_replace present in v4_zones.py for patch subcommand
