# Phase 07: License Management - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning
**Mode:** Auto-generated (smart discuss — plan pre-exists, established pattern)

<domain>
## Phase Boundary

A single `v4_license.py` command with 9 subcommands covering license CRUD, lease management, and activation lifecycle operations.

</domain>

<decisions>
## Implementation Decisions

### Workspace scoping (nuanced for leases)
- `leases-ls`: workspaceId is **optional** query param — if workspace is set, include it; if not, omit (do NOT raise an error)
- `leases-create`: workspaceId **required** in body — use `v4_inject_workspace()`
- All other subcommands: NO workspace required

### Optional workspace pattern for leases-ls
Use `user_data.get_meta('workspace id')` and only add to params if non-None:
```python
params = {}
ws_id = user_data.get_meta('workspace id')
if ws_id:
    params['workspaceId'] = ws_id
```

### Confirmed (consistent with prior phases)
- **Additive only** — zero modifications to any existing file
- **File naming** — `v4_license.py` in `neoload/commands/`
- **Auto-discovery** — CLI plugin loader picks up files automatically
- **--file flag** for JSON body inputs

</decisions>

<code_context>
## Existing Code Insights

The optional workspace pattern differs from `v4_workspace_params()` which raises an error if not set.

</code_context>

<specifics>
## Specific Requirements

Per plan 07-01-PLAN.md — 1 command file, 9 subcommands.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
