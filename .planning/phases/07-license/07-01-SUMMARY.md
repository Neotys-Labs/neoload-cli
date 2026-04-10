---
phase: 07-license
plan: "07-01"
subsystem: api
tags: [click, python, license, leases, v4-api]

# Dependency graph
requires:
  - phase: 01-v4-foundation
    provides: v4_endpoints helpers (v4_endpoint, v4_inject_workspace, v4_workspace_params)
provides:
  - neoload v4-license command with 9 subcommands for license management and lease operations
affects: [08-users, 09-me, 10-settings]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Optional workspace query param: check user_data.get_meta() and include only if present"
    - "Mandatory workspace body injection: v4_inject_workspace() raises if not set"
    - "Subcommand dispatch via click.Choice argument with set_current_sub_command tracking"

key-files:
  created:
    - neoload/commands/v4_license.py
  modified: []

key-decisions:
  - "leases-ls uses optional workspaceId: admins may omit workspace to list all leases globally"
  - "leases-create uses v4_inject_workspace: workspace is required for offline lease scoping"
  - "leases-get takes positional lease_identifier argument matching existing v4 command pattern"

patterns-established:
  - "Optional workspace param pattern: {workspaceId: id} if id else None passed to rest_crud.get"

requirements-completed: []

# Metrics
duration: 8min
completed: 2026-04-10
---

# Phase 7 Plan 01: License Management Summary

**v4-license Click command covering all 9 license/lease subcommands: get, install, leases-ls (workspace optional), leases-create (workspace required), leases-get by ID, activation-request, deactivation-request, forced-release, release**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-10T00:00:00Z
- **Completed:** 2026-04-10T00:08:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created `v4_license.py` with all 9 subcommands following established v4 command patterns
- Implemented optional workspace query param for `leases-ls` (admins may omit workspace)
- Implemented mandatory workspace body injection for `leases-create` via `v4_inject_workspace`
- Positional `lease_identifier` argument for `leases-get` follows existing v4 reservations pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: v4-license command** - `ccaad20` (feat)

## Files Created/Modified
- `neoload/commands/v4_license.py` - v4-license Click command: 9 subcommands for license management, lease CRUD, and activation lifecycle

## Decisions Made
- `leases-ls` uses optional workspaceId: check `user_data.get_meta('workspace id')` and include only if set, passing `None` to `rest_crud.get` otherwise. This allows admin-level listing without a workspace context.
- `leases-create` uses `v4_inject_workspace()` which raises `CliException` if workspace is not set — workspace is mandatory in the POST body.
- All other subcommands (get, install, activation-request, etc.) operate at the global license level with no workspace param.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- v4-license command complete and accessible as `neoload v4-license`
- Follows the same patterns as v4-reservations and v4-analytics for consistency
- Ready for phase 08 (users) and beyond

---
*Phase: 07-license*
*Completed: 2026-04-10*
