# Phase 06: Infrastructure - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning
**Mode:** Auto-generated (smart discuss — plan pre-exists, established pattern)

<domain>
## Phase Boundary

Add v4 CLI commands for proxies, infrastructure providers, and guaranteed resources.

Key distinction: guaranteed resources use workspaceId as a **path parameter** (embedded in the URL), unlike phases 4-5 where workspace was injected as query/body.

</domain>

<decisions>
## Implementation Decisions

### Workspace pattern (unique to this phase)
- **Proxies**: No workspaceId at all — plain `v4_endpoint('proxies', ...)`
- **Infrastructure providers**: No workspaceId — plain `v4_endpoint('infrastructure-providers', ...)`
- **Guaranteed resources**: workspaceId is a PATH param — `v4_endpoint('workspaces', workspace_id, 'guaranteed-resources', ...)` — NOT `v4_workspace_params()` or `v4_inject_workspace()`

### Getting workspace_id for guaranteed resources
- Read from `user_data.get_meta('workspace id')` directly (same source as `v4_workspace_params()`)
- Raise `CliException` if not set, with message: "No workspace set. Please use 'neoload workspaces use <id>' first."

### Confirmed (consistent with prior phases)
- **Additive only** — zero modifications to any existing file
- **File naming** — `v4_proxies.py`, `v4_infrastructure_providers.py`, `v4_guaranteed_resources.py`
- **Auto-discovery** — CLI plugin loader picks up files automatically
- **HTTP pattern** — use `v4_endpoint()` + `rest_crud()` from the shared helper layer

</decisions>

<code_context>
## Existing Code Insights

Guaranteed resources endpoint pattern: `v4/workspaces/{workspaceId}/guaranteed-resources`
This is built as: `v4_endpoint('workspaces', workspace_id, 'guaranteed-resources')`

</code_context>

<specifics>
## Specific Requirements

Per plan 06-01-PLAN.md — 3 command files, 12 total subcommands.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
