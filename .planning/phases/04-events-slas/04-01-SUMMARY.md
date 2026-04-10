---
phase: "04-events-slas"
plan: "04-01"
subsystem: "events-slas"
tags: ["v4", "events", "slas", "cli", "results"]
dependency_graph:
  requires: ["01-01", "01-02"]
  provides: ["v4-events-command", "v4-slas-command"]
  affects: []
tech_stack:
  added: []
  patterns: ["Click argument-based subcommands", "v4_endpoints helper", "result-scoped endpoints"]
key_files:
  created:
    - neoload/commands/v4_events.py
    - neoload/commands/v4_slas.py
  modified: []
decisions:
  - "Used argument-based subcommands (same pattern as v4_analytics.py) for consistency"
  - "delete subcommand checks for 204/empty body before attempting JSON parse"
  - "No workspaceId injection — all endpoints are result-scoped"
metrics:
  duration: "~5 minutes"
  completed_date: "2026-04-10"
  tasks_completed: 2
  files_created: 2
  files_modified: 0
---

# Phase 4 Plan 1: Events and SLAs Summary

**One-liner:** Two result-scoped v4 CLI commands — v4-events (8 subcommands for full event CRUD + aggregations) and v4-slas (ls only).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | v4-events command | 5797872 | neoload/commands/v4_events.py |
| 2 | v4-slas command | 85eebe7 | neoload/commands/v4_slas.py |

## What Was Built

### v4-events (`neoload v4-events`)

Full CRUD plus aggregation subcommands for `/v4/results/{resultId}/events`:

- `ls` — GET /v4/results/{resultId}/events
- `create` — POST /v4/results/{resultId}/events (--file for JSON body)
- `get` — GET /v4/results/{resultId}/events/{eventId} (requires --event-id)
- `patch` — PATCH /v4/results/{resultId}/events/{eventId} (requires --event-id, --file)
- `delete` — DELETE /v4/results/{resultId}/events/{eventId} (requires --event-id)
- `errors` — GET /v4/results/{resultId}/events/errors
- `statistics` — GET /v4/results/{resultId}/events/statistics
- `content` — GET /v4/results/{resultId}/events/contents/{contentId} (requires --content-id)

### v4-slas (`neoload v4-slas`)

Single listing subcommand for `/v4/results/{resultId}/slas`:

- `ls` — GET /v4/results/{resultId}/slas

## Verification

- All subcommands accessible and display help text: PASSED
- No existing files modified: PASSED (git diff shows only 2 new files added)
- All endpoints correctly scoped by resultId with no workspaceId needed: PASSED

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — all endpoints are read/write against existing result resources, no new trust boundaries introduced.

## Self-Check: PASSED

- neoload/commands/v4_events.py: FOUND
- neoload/commands/v4_slas.py: FOUND
- Commit 5797872: FOUND
- Commit 85eebe7: FOUND
