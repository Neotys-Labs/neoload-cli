---
phase: 02-core-resources
plan: "03"
subsystem: v4-test-executions
tags: [v4, test-executions, cli, polling, logs-streaming, ci-cd]
dependency_graph:
  requires:
    - neoload/neoload_cli_lib/v4/v4_client.py
    - neoload/neoload_cli_lib/v4/v4_endpoints.py
    - neoload/neoload_cli_lib/rest_crud.py
    - neoload/neoload_cli_lib/tools.py
    - neoload/neoload_cli_lib/cli_exception.py
  provides:
    - neoload/commands/v4_test_executions.py
  affects: []
tech_stack:
  added: []
  patterns:
    - click.Choice argument-based dispatch (consistent with v2/v3 pattern)
    - TERMINAL_STEPS/FAIL_EXIT_STEPS sentinel sets for polling loop exit logic
    - rest_crud.post direct (no workspaceId injection for test-executions create)
    - v4_client.v4_get for polling (no workspace needed for by-ID lookups)
    - rest_crud.get with params for paginated logs endpoint
key_files:
  created:
    - neoload/commands/v4_test_executions.py
    - tests/commands/test_v4_test_executions.py
  modified: []
decisions:
  - "Used rest_crud.post directly (not v4_client.v4_create) for create: POST /v4/test-executions does not need workspaceId injection per API spec"
  - "FAIL_EXIT_STEPS = {'FAILED', 'CANCELLED'} per D-05 user confirmation: CANCELLED is the v4 API equivalent of TERMINATED"
  - "STARTED_TEST in TERMINAL_STEPS (terminal from launcher perspective) but NOT in FAIL_EXIT_STEPS (exit 0)"
  - "logs polling uses rest_crud.get directly (not v4_client.v4_get) because v4_get takes no params argument; logs needs pageNumber/pageSize params"
metrics:
  duration: "~5 minutes"
  completed: "2026-04-09"
  tasks_completed: 2
  files_created: 2
  files_modified: 0
---

# Phase 02 Plan 03: v4-test-executions Command Summary

**One-liner:** v4-test-executions CLI command with 5 subcommands including --wait CI polling (exit 1 on FAILED/CANCELLED per D-05) and paginated logs streaming via rest_crud.get.

## What Was Built

Implemented `neoload/commands/v4_test_executions.py` — the most complex command file in Phase 2, providing:

1. **create** — POSTs to `/v4/test-executions` via `rest_crud.post` (no workspaceId injection). Accepts `--test-id`, `--scenario` (-> `scenarioName`), `--zone-type` (-> `zoneType`), plus optional `--file` for full JSON body.

2. **create --wait** — After POST, polls `GET /v4/test-executions/{id}` every 5 seconds until a terminal step is reached. Exits 1 on `FAILED` or `CANCELLED` (per D-05 user-confirmed mapping); exits 0 on `STARTED_TEST` or other terminal steps.

3. **get** — Calls `v4_client.v4_get('test-executions', id)` and prints result.

4. **cancel** — Calls `rest_crud.delete` on `/v4/test-executions/{id}`. Handles 202 with empty body by printing confirmation message.

5. **force-cancel** — Calls `rest_crud.delete` on `/v4/test-executions/{id}/forced`. Same 202 handling.

6. **logs** — Polls `GET /v4/results/{resultId}/logs` with pageNumber pagination via `rest_crud.get`. Prints each log entry as formatted `{date} {level} {line}` line. Stops when all pages fetched.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create v4_test_executions.py | d86954c | neoload/commands/v4_test_executions.py |
| 2 | Create test_v4_test_executions.py | e685419 | tests/commands/test_v4_test_executions.py |

## Verification Results

- `python3 -c "from commands.v4_test_executions import cli"` — OK
- `pytest tests/commands/test_v4_test_executions.py -x -q` — 15 passed
- `FAIL_EXIT_STEPS` contains `'FAILED'` and `'CANCELLED'` — Verified
- No `v4_client.v4_create` usage — Verified (uses `rest_crud.post` directly)
- `scenarioName` and `zoneType` body fields — Verified

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all subcommands are fully implemented with real API calls.

## Threat Flags

No new threat surface introduced beyond what is documented in the plan's threat model. The implementation includes:
- JSON validation via `json.load()` for `--file` input (mitigates T-02-07)
- ID passed through `v4_endpoint` path join without additional transformation (T-02-08 accepted)
- `TERMINAL_STEPS` set covers all terminal states from API spec enum (mitigates T-02-09)

## Self-Check: PASSED

Files created:
- FOUND: neoload/commands/v4_test_executions.py
- FOUND: tests/commands/test_v4_test_executions.py

Commits exist:
- FOUND: d86954c (feat(02-03): implement v4-test-executions command with 5 subcommands)
- FOUND: e685419 (test(02-03): add unit tests for v4-test-executions command)
