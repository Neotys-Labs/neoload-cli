---
phase: 02-core-resources
plan: "04"
subsystem: v4-workspaces
tags: [cli, v4, workspaces, members, rest_crud]
dependency_graph:
  requires: []
  provides: [v4-workspaces-command]
  affects: []
tech_stack:
  added: []
  patterns: [click-command, manual-pagination, url-encoding]
key_files:
  created:
    - neoload/commands/v4_workspaces.py
    - tests/commands/test_v4_workspaces.py
  modified: []
decisions:
  - "Workspaces are NOT workspace-scoped: ls and create use rest_crud directly without workspaceId injection"
  - "members-add uses rest_crud.post directly (not v4_create) to avoid workspaceId being injected into POST body"
  - "members-remove encodes login via urllib.parse.urlencode into URL query string since rest_crud.delete has no params argument"
metrics:
  duration: "~3 minutes"
  completed_date: "2026-04-09"
  tasks_completed: 2
  files_created: 2
  files_modified: 0
---

# Phase 02 Plan 04: v4-workspaces Command Summary

**One-liner:** v4-workspaces CLI with 9 subcommands using direct rest_crud calls (no workspaceId injection) and urllib.parse.urlencode for safe login URL encoding in members-remove.

## What Was Built

Implemented the `v4-workspaces` CLI command (`neoload/commands/v4_workspaces.py`) providing complete workspace management with 9 subcommands, and 16 passing unit tests (`tests/commands/test_v4_workspaces.py`).

### Subcommands

| Subcommand | HTTP Method | Helper Used | Notes |
|---|---|---|---|
| ls | GET paginated | `rest_crud.get` | Manual pagination, no workspaceId |
| create | POST | `rest_crud.post` | No workspaceId in body |
| get | GET single | `v4_client.v4_get` | By ID |
| patch | PATCH | `v4_client.v4_update` | By ID |
| delete | DELETE | `v4_client.v4_delete` | Returns None on 204 |
| members-ls | GET | `v4_client.v4_get` | workspaces/{id}/members |
| members-add | POST | `rest_crud.post` | Body: {userId, role}, no workspaceId |
| members-remove | DELETE | `rest_crud.delete` | login URL-encoded as query param |
| subscription | GET | `v4_client.v4_get` | workspaces/{id}/subscription |

## Key Implementation Details

**Why direct rest_crud for ls/create?**
`v4_client.v4_list` injects `workspaceId` as a query param — incorrect for workspace listing. `v4_client.v4_create` injects `workspaceId` into the POST body — incorrect for workspace creation. Both operations use `rest_crud` directly.

**Why direct rest_crud for members-add?**
`v4_client.v4_create` would inject `workspaceId` into the body, but the members-add API expects `{userId, role}` only. Using `rest_crud.post` directly avoids this injection.

**Why urllib.parse.urlencode for members-remove?**
`rest_crud.delete` has no `params` argument (unlike `rest_crud.get`). The login value must be encoded into the URL query string directly using `urllib.parse.urlencode({'login': login})` to safely handle special characters like `@`, `+`, spaces.

## Decisions Made

1. Used `@click.command()` (not `@click.group()`) with a `command` Choice argument — matches existing v2/v3 pattern in `workspaces.py`
2. `_workspace_list()` helper handles manual pagination separately from `_build_body()` for create/patch
3. `members-remove` calls `rest_crud.delete` with the raw response; checks `response.content` to handle 204 No Content gracefully

## Threat Mitigations Implemented

| Threat ID | Mitigation |
|---|---|
| T-02-11 | `json.load()` in `_build_body` and `members-add` handler raises `CliException` on malformed JSON |
| T-02-12 | `urllib.parse.urlencode({'login': login})` safely encodes `@`, `+`, spaces, `&` preventing URL injection |

## Deviations from Plan

None — plan executed exactly as written.

## Test Coverage

16 tests in `TestV4Workspaces` class:
- `test_ls` — single page pagination
- `test_ls_multi_page` — verifies pagination loop
- `test_create` — verifies body sent with name
- `test_create_no_workspace_id_injected` — key invariant: no workspaceId
- `test_get` — by ID lookup
- `test_patch` — name update
- `test_delete` — None result (204)
- `test_delete_with_body` — non-empty result
- `test_members_ls` — endpoint path contains workspaces/id/members
- `test_members_add` — body has no workspaceId (key invariant)
- `test_members_add_no_file_raises` — error handling
- `test_members_remove` — endpoint contains login=
- `test_members_remove_url_encodes_special_chars` — URL encoding for `+` and `@`
- `test_members_remove_no_login_raises` — error handling
- `test_subscription` — endpoint path contains workspaces/id/subscription
- `test_missing_command` — no-command guard

## Self-Check: PASSED

- `neoload/commands/v4_workspaces.py` exists: FOUND
- `tests/commands/test_v4_workspaces.py` exists: FOUND
- Commit `3163759` (feat): FOUND
- Commit `c33eec2` (test): FOUND
- pytest: 16 passed
