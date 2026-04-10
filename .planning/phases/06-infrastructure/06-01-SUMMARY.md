---
phase: "06-infrastructure"
plan: "06-01"
subsystem: "infrastructure"
tags: ["v4", "proxies", "infrastructure-providers", "guaranteed-resources", "click"]
dependency_graph:
  requires: ["01-01"]
  provides: ["v4-proxies", "v4-infrastructure-providers", "v4-guaranteed-resources"]
  affects: []
tech_stack:
  added: []
  patterns: ["no-workspace-flat-crud", "workspace-as-path-param"]
key_files:
  created:
    - neoload/commands/v4_proxies.py
    - neoload/commands/v4_infrastructure_providers.py
    - neoload/commands/v4_guaranteed_resources.py
  modified: []
decisions:
  - "Guaranteed resources use workspace_id as path parameter (not query param or body injection) because the API path is /v4/workspaces/{workspaceId}/guaranteed-resources"
  - "Proxies and infrastructure-providers have no workspace scope — ls/create/patch/delete all use flat /v4/{resource} paths"
  - "Guaranteed resources patch/delete have no sub-resource ID param — the API path has no {id} segment (workspace-level resource)"
metrics:
  duration_seconds: 60
  completed_date: "2026-04-10"
  tasks_completed: 3
  files_created: 3
  files_modified: 0
---

# Phase 6 Plan 1: Infrastructure Summary

Three v4 CLI commands for infrastructure management — proxies (flat CRUD), infrastructure providers (flat CRUD), and guaranteed resources (workspace-scoped path-param CRUD).

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | v4-proxies (ls/create/patch/delete) | 5b3159d | neoload/commands/v4_proxies.py |
| 2 | v4-infrastructure-providers (ls/create/patch/delete) | 55abb15 | neoload/commands/v4_infrastructure_providers.py |
| 3 | v4-guaranteed-resources (ls/create/patch/delete) | 6a2d584 | neoload/commands/v4_guaranteed_resources.py |

## Implementation Notes

### Proxies (`v4_proxies.py`)

Flat CRUD with no workspace scope:
- `ls` — `GET /v4/proxies`
- `create` — `POST /v4/proxies` (--file for JSON body)
- `patch` — `PATCH /v4/proxies/{proxyId}` (requires proxy_id argument)
- `delete` — `DELETE /v4/proxies/{proxyId}` (requires proxy_id argument)

### Infrastructure Providers (`v4_infrastructure_providers.py`)

Flat CRUD with no workspace scope:
- `ls` — `GET /v4/infrastructure-providers`
- `create` — `POST /v4/infrastructure-providers` (--file for JSON body)
- `patch` — `PATCH /v4/infrastructure-providers/{id}` (requires provider_id argument)
- `delete` — `DELETE /v4/infrastructure-providers/{id}` (requires provider_id argument)

### Guaranteed Resources (`v4_guaranteed_resources.py`)

Workspace-scoped with workspaceId as path parameter. Reads workspace_id from `user_data.get_meta('workspace id')` and raises `CliException` if not set:
- `ls` — `GET /v4/workspaces/{workspaceId}/guaranteed-resources`
- `create` — `POST /v4/workspaces/{workspaceId}/guaranteed-resources` (--file for JSON body)
- `patch` — `PATCH /v4/workspaces/{workspaceId}/guaranteed-resources` (--file for JSON body)
- `delete` — `DELETE /v4/workspaces/{workspaceId}/guaranteed-resources`

Note: guaranteed-resources patch/delete operate at the workspace level with no sub-resource ID (unlike proxies/providers which target individual resource IDs).

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints beyond the three commands described in the plan. No auth paths, file access patterns, or schema changes introduced.

## Self-Check: PASSED

- neoload/commands/v4_proxies.py — FOUND
- neoload/commands/v4_infrastructure_providers.py — FOUND
- neoload/commands/v4_guaranteed_resources.py — FOUND
- Commit 5b3159d (v4-proxies) — FOUND
- Commit 55abb15 (v4-infrastructure-providers) — FOUND
- Commit 6a2d584 (v4-guaranteed-resources) — FOUND
- No existing files modified — VERIFIED (git diff shows only 3 new files)
