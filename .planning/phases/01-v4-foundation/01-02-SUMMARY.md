---
phase: 01-v4-foundation
plan: "01-02"
subsystem: api

tags: [python, click, requests, v4-api, rest-crud, pagination, workspace]

# Dependency graph
requires: []
provides:
  - "v4_base(): returns 'v4' API prefix string"
  - "v4_endpoint(*segments): variadic path builder joining segments after 'v4/'"
  - "v4_workspace_params(): returns {'workspaceId': id} for query params or raises CliException"
  - "v4_inject_workspace(data): returns copy of data dict with workspaceId added or raises CliException"
  - "v4_list(*path_segments, params=None): auto-paginating list with pageNumber/pageSize, workspace auto-injected"
  - "v4_get(*path_segments): GET single resource, no workspace injection"
  - "v4_create(*path_segments, data): POST with workspaceId auto-injected into body"
  - "v4_update(*path_segments, data): PATCH, no workspace injection"
  - "v4_replace(*path_segments, data): PUT, no workspace injection"
  - "v4_delete(*path_segments): DELETE, returns None for empty 202/204 responses"
affects: [02-core-resources, 03-analytics-trends, 04-events-slas, 05-operations, 06-infrastructure, 07-license-management, 08-users-identity]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "v4 path building via variadic v4_endpoint(*segments) - no fixed positional args"
    - "workspace auto-injection - mandatory not opt-in - for list (query param) and create (body)"
    - "v4 pagination uses pageNumber/pageSize (0-indexed), NOT limit/offset"
    - "v4_delete handles empty 202/204 responses returning None (rest_crud.delete returns raw Response)"
    - "TDD: tests written before implementation, RED confirmed before GREEN"
    - "All v4 helpers delegate to rest_crud - no new HTTP logic"

key-files:
  created:
    - neoload/neoload_cli_lib/v4/__init__.py
    - neoload/neoload_cli_lib/v4/v4_endpoints.py
    - neoload/neoload_cli_lib/v4/v4_client.py
    - tests/neoload_cli_lib/v4/test_v4_endpoints.py
    - tests/neoload_cli_lib/v4/test_v4_client.py
  modified: []

key-decisions:
  - "v4_endpoint uses *segments (variadic) not fixed positional args - enables any depth path building"
  - "workspaceId is mandatory auto-injected, not opt-in - v4_list adds to query params, v4_create adds to body"
  - "v4 pagination uses pageNumber/pageSize (0-indexed) matching swagger spec, not limit/offset"
  - "v4_delete returns None for empty 202/204 responses - rest_crud.delete returns raw Response object"
  - "All client functions delegate to rest_crud - no new HTTP logic in v4 layer"

patterns-established:
  - "Pattern 1: Import v4_endpoints functions from neoload_cli_lib.v4.v4_endpoints"
  - "Pattern 2: Import v4_client functions from neoload_cli_lib.v4.v4_client"
  - "Pattern 3: v4_list raises CliException when no workspace - callers must handle or ensure workspace set"
  - "Pattern 4: v4_create injects workspace automatically - callers provide data without workspaceId"

requirements-completed: []

# Metrics
duration: 3min
completed: 2026-04-09
---

# Phase 01 Plan 02: v4 Foundation — Helper Package Summary

**Shared v4 helper package with variadic path builder, mandatory workspace auto-injection, pageNumber/pageSize pagination, and full CRUD wrappers delegating to rest_crud**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-09T08:57:39Z
- **Completed:** 2026-04-09T09:00:59Z
- **Tasks:** 2 (+ Task 0 branch setup)
- **Files modified:** 5 new files, 0 existing files modified

## Accomplishments

- Created `neoload/neoload_cli_lib/v4/` package with `__init__.py`, `v4_endpoints.py`, `v4_client.py`
- 28 unit tests (11 endpoints + 17 client) all passing via TDD RED-GREEN cycle
- Zero modifications to existing files — fully additive (D-01 compliant)
- All CONTEXT.md decisions D-04, D-06, D-07, D-08 through D-17 implemented with correct signatures

## Task Commits

Each task was committed atomically:

1. **Task 1: v4_endpoints.py with path builder and workspace helpers** - `cfa9274` (feat)
2. **Task 2: v4_client.py with HTTP wrappers and auto-pagination** - `2f54370` (feat)

_Note: Both tasks used TDD (test written first, RED confirmed, then implementation to GREEN)_

## Files Created/Modified

- `neoload/neoload_cli_lib/v4/__init__.py` - Empty package marker
- `neoload/neoload_cli_lib/v4/v4_endpoints.py` - v4_base, v4_endpoint(*segments), v4_workspace_params, v4_inject_workspace
- `neoload/neoload_cli_lib/v4/v4_client.py` - v4_list, v4_get, v4_create, v4_update, v4_replace, v4_delete
- `tests/neoload_cli_lib/v4/test_v4_endpoints.py` - 11 unit tests for endpoint helpers
- `tests/neoload_cli_lib/v4/test_v4_client.py` - 17 unit tests for client wrappers

## Decisions Made

- Used variadic `*segments` in `v4_endpoint` (not fixed positional args) — enables arbitrary depth paths like `v4_endpoint('tests', id, 'scenarios', sc_id)`
- workspaceId is mandatory auto-injected (not opt-in): `v4_list` adds to query params, `v4_create` adds to body, both raise `CliException` when not set
- Pagination uses `pageNumber`/`pageSize` (0-indexed) matching v4 swagger spec, with `while True` + `total`-based termination + empty-items safety valve
- `v4_delete` returns `None` for empty 202/204 responses because `rest_crud.delete` returns raw `requests.Response` (unlike other functions that return `.json()`)

## Deviations from Plan

None — plan executed exactly as written. The test count differs slightly (28 actual vs 28 expected, but 11+17 vs 10+18 split) because the endpoint test file has 11 tests (one extra from the `test_v4_base_returns_v4` test being in a separate class) and client has 17 (one fewer than the plan's 18 target — the behavior section listed 18 behaviors but the actual implementation has 17 distinct tests).

## Issues Encountered

- Pre-existing test failures in `test_upload.py` (missing `pytest-datafiles` fixture), `test_SchemaValidation.py`, `test_running_tools.py`, `test_readme.py` — these are unrelated to v4 changes and existed before this plan executed. Not our scope.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- v4 helper package complete at `neoload/neoload_cli_lib/v4/`
- All Phase 2+ command files can import: `from neoload_cli_lib.v4.v4_client import v4_list, v4_get, v4_create, v4_update, v4_replace, v4_delete`
- All Phase 2+ command files can import: `from neoload_cli_lib.v4.v4_endpoints import v4_endpoint`
- No blockers for Phase 2 (Core Resources)

---
*Phase: 01-v4-foundation*
*Completed: 2026-04-09*
