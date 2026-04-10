# Phase 05: Operations - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning
**Mode:** Auto-generated (smart discuss — plan pre-exists, established pattern)

<domain>
## Phase Boundary

Add v4 CLI commands for webhooks, SCM repositories, reservations, and deletion policies. This phase introduces the first commands that require workspaceId injection on certain operations.

</domain>

<decisions>
## Implementation Decisions

### Workspace scoping rules (key distinction from phases 3–4)
- **Webhooks**: `ls` uses `v4_workspace_params()` (query param), `create` uses `v4_inject_workspace()` (body); `get/patch/delete/validate` use no workspace
- **SCM repositories**: No workspaceId on any endpoint
- **Reservations**: `ls` uses `v4_workspace_params()`, `create` uses `v4_inject_workspace()`; `get/patch/delete` use no workspace
- **Deletion policies**: `ls` uses `v4_workspace_params()`, `create`/`dry-run` use `v4_inject_workspace()`; `get/patch/delete` use no workspace

### Confirmed (consistent with prior phases)
- **Additive only** — zero modifications to any existing file
- **File naming** — `v4_webhooks.py`, `v4_scm_repositories.py`, `v4_reservations.py`, `v4_deletion_policies.py`
- **Auto-discovery** — CLI plugin loader picks up files automatically
- **HTTP pattern** — use `v4_endpoint()` + `rest_crud()` from the shared helper layer
- **JSON body option** — `--file` flag for POST/PATCH payloads

</decisions>

<code_context>
## Existing Code Insights

- `v4_workspace_params()` returns `{'workspaceId': id}` for use as query params
- `v4_inject_workspace(data)` injects workspaceId into a body dict
- Both are in `neoload/neoload_cli_lib/v4/v4_endpoints.py`

</code_context>

<specifics>
## Specific Requirements

Per plan 05-01-PLAN.md — 4 command files, 24 total subcommands.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
