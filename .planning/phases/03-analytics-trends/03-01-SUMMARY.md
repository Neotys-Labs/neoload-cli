---
phase: "03-analytics-trends"
plan: "03-01"
subsystem: "analytics-trends"
tags: ["v4", "analytics", "trends", "cli"]
dependency_graph:
  requires: ["02-01"]
  provides: ["v4-analytics-command", "v4-trends-command"]
  affects: []
tech_stack:
  added: []
  patterns: ["click-plugin-command", "rest-crud-direct", "resultId-scoped", "testId-scoped"]
key_files:
  created:
    - neoload/commands/v4_analytics.py
    - neoload/commands/v4_trends.py
  modified: []
decisions:
  - "Used rest_crud directly (not v4_client) for analytics/trends — no workspaceId injection needed"
  - "intervals-ls returns raw response (not paginated list) — consistent with similar non-list endpoints"
metrics:
  duration: "1 minute"
  completed: "2026-04-10"
  tasks_completed: 2
  files_created: 2
  files_modified: 0
---

# Phase 3 Plan 1: Analytics and Trends Summary

v4-analytics (11 subcommands, resultId-scoped) and v4-trends (6 subcommands, testId-scoped) CLI commands added as new plugin files with zero modifications to existing code.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | v4-analytics command | 3a73f5c | neoload/commands/v4_analytics.py |
| 2 | v4-trends command | 33a15f1 | neoload/commands/v4_trends.py |

## What Was Built

### v4-analytics (`neoload v4-analytics`)

11 subcommands for result analytics, all scoped via `--result-id`:

- `element-values` — GET /v4/results/{resultId}/elements/values
- `element-timeseries` — GET /v4/results/{resultId}/elements/{elementId}/timeseries (requires `--element-id`)
- `element-percentiles` — GET /v4/results/{resultId}/elements/{elementId}/percentiles (requires `--element-id`)
- `monitor-values` — GET /v4/results/{resultId}/monitors/values
- `monitor-timeseries` — GET /v4/results/{resultId}/monitors/{monitorId}/timeseries (requires `--monitor-id`)
- `intervals-ls` — GET /v4/results/{resultId}/intervals
- `intervals-create` — POST /v4/results/{resultId}/intervals (optional `--file` for JSON body)
- `intervals-patch` — PATCH /v4/results/{resultId}/intervals/{intervalId} (requires `--interval-id`)
- `intervals-delete` — DELETE /v4/results/{resultId}/intervals/{intervalId} (requires `--interval-id`)
- `interval-generation` — POST /v4/results/{resultId}/interval-generation (optional `--file`)
- `report` — POST /v4/results/{resultId}/report (optional `--file`)

### v4-trends (`neoload v4-trends`)

6 subcommands for test trends, all scoped via `--test-id`:

- `get` — GET /v4/tests/{testId}/trends
- `patch` — PATCH /v4/tests/{testId}/trends (optional `--file`)
- `config-get` — GET /v4/tests/{testId}/trends/configuration
- `config-put` — PUT /v4/tests/{testId}/trends/configuration (optional `--file`, `--dry-run` adds `?dryRun=true`)
- `config-patch` — PATCH /v4/tests/{testId}/trends/configuration (optional `--file`)
- `elements` — GET /v4/tests/{testId}/trends/elements

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Used `rest_crud` directly instead of `v4_client` wrappers | Analytics and trends are scoped by resultId/testId — no workspaceId injection needed; direct REST calls are clearer |
| `--result-id` and `--test-id` as required options (not arguments) | Consistent with plan spec; named options are more readable in scripts |
| `--dry-run` flag appends `?dryRun=true` to endpoint URL | Query param approach consistent with existing v4 patterns (e.g., `?deleteResults=true` in v4_tests) |

## Verification

- Both commands display complete help text with all subcommands listed
- `v4_analytics.py` exposes `neoload v4-analytics` via auto-discovery plugin mechanism
- `v4_trends.py` exposes `neoload v4-trends` via auto-discovery plugin mechanism
- No existing files modified — `git status` shows only two new untracked files before commit

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all commands wire directly to API endpoints via rest_crud.

## Threat Flags

None — no new auth paths or trust boundaries introduced. All endpoints require existing accountToken auth (handled by rest_crud layer). No new data storage or file access patterns.

## Self-Check: PASSED

- [x] neoload/commands/v4_analytics.py exists — FOUND
- [x] neoload/commands/v4_trends.py exists — FOUND
- [x] Commit 3a73f5c exists — FOUND
- [x] Commit 33a15f1 exists — FOUND
- [x] No existing files modified — confirmed via git status
