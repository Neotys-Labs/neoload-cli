# Phase 04: Events and SLAs - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning
**Mode:** Auto-generated (smart discuss — plan pre-exists, established pattern)

<domain>
## Phase Boundary

Add v4 CLI commands for result events and SLA data, scoped by `--result-id`. Follows the same additive, zero-modification pattern established in phases 1–3.

- `v4-events`: 8 subcommands for CRUD + error/statistics/content aggregation
- `v4-slas`: 1 subcommand (ls) for SLA listing

</domain>

<decisions>
## Implementation Decisions

### Confirmed (consistent with prior phases)
- **Additive only** — zero modifications to any existing file
- **resultId scoping** — `--result-id` required, no workspaceId injection
- **File naming** — `v4_events.py` and `v4_slas.py` in `neoload/commands/`
- **Auto-discovery** — CLI plugin loader picks up files automatically; no manual registration
- **HTTP pattern** — use `v4_endpoint()` + `rest_crud()` from the shared helper layer
- **JSON body option** — `--file` flag for POST/PATCH payloads (consistent with other v4 commands)

</decisions>

<code_context>
## Existing Code Insights

Follows the pattern from v4_analytics.py and v4_trends.py (phase 3):
- Import `v4_endpoint` from `neoload.neoload_cli_lib.v4.v4_endpoints`
- Import `rest_crud` from `neoload.neoload_cli_lib.rest_crud`
- Expose a `cli` Click group with subcommands

</code_context>

<specifics>
## Specific Requirements

- `v4-events ls` → GET /v4/results/{resultId}/events
- `v4-events create` → POST /v4/results/{resultId}/events (--file body)
- `v4-events get` → GET /v4/results/{resultId}/events/{eventId}
- `v4-events patch` → PATCH /v4/results/{resultId}/events/{eventId} (--file body)
- `v4-events delete` → DELETE /v4/results/{resultId}/events/{eventId}
- `v4-events errors` → GET /v4/results/{resultId}/events/errors
- `v4-events statistics` → GET /v4/results/{resultId}/events/statistics
- `v4-events content` → GET /v4/results/{resultId}/events/contents/{contentId}
- `v4-slas ls` → GET /v4/results/{resultId}/slas

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
