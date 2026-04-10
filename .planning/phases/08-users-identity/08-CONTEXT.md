# Phase 08: Users and Identity - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning
**Mode:** Auto-generated (smart discuss — plan pre-exists, established pattern)

<domain>
## Phase Boundary

6 new command files covering user management, personal profile (me), sessions, account settings, SSO configuration, and LDAP integration. All endpoints are workspace-free — purely user/identity scoped operations.

</domain>

<decisions>
## Implementation Decisions

### No workspace injection anywhere
All 6 files use plain `v4_endpoint()` calls with no `v4_workspace_params()` or `v4_inject_workspace()`.

### Special note: users workspaces-add
`workspaces-add` sends `PUT /v4/users/{userId}/workspaces` with workspaceId in the body, but this is user-supplied via `--file` (not injected from stored workspace). Not a "workspace scoped" operation.

### Confirmed (consistent with prior phases)
- **Additive only** — zero modifications to any existing file
- **File naming** — 6 files, all `v4_*.py` in `neoload/commands/`
- **Auto-discovery** — CLI plugin loader picks up files automatically
- **--file flag** for JSON body inputs

</decisions>

<code_context>
## Existing Code Insights

Large phase — 6 files, ~37 subcommands total. Follow the same pattern as v4_analytics.py (no workspace). Users file has a sub-resource (workspaces) that takes path params.

</code_context>

<specifics>
## Specific Requirements

Per plan 08-01-PLAN.md — 6 command files, ~37 total subcommands.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
