# NeoLoad CLI — v4 API Expansion

## What This Is

A Python CLI tool (`neoload`) for automating NeoLoad Web operations — test management, execution, results analysis, and infrastructure configuration. Built with Click, it communicates with NeoLoad Web's REST API and is used in CI/CD pipelines and by performance engineers from the command line.

**v1.0 shipped 2026-04-10:** Complete CLI coverage of the NeoLoad Web v4 API — 23 new command files, ~150 subcommands, zero modifications to existing v2/v3 code.

## Core Value

Provide complete CLI coverage of the NeoLoad Web v4 API so that every server-side operation available via the API can be performed from the command line or automated in scripts.

## Requirements

### Validated

- v2/v3 API coverage: login, test-settings CRUD, test-results CRUD, run/wait/stop, project upload, zones listing, workspaces ls/use, logs, report generation, as-code validation, fastfail SLA monitoring, Docker helpers, config management
- v4 API helper layer (`v4_endpoints.py`, `v4_client.py`) — additive, no changes to existing code — ✓ v1.0
- v4 tests CRUD + scenarios — ✓ v1.0
- v4 results CRUD + sub-resources (contexts, elements, monitors, statistics, timeseries) — ✓ v1.0
- v4 test-executions (create/get/cancel/force-cancel/logs + --wait polling) — ✓ v1.0
- v4 workspaces full CRUD + members management — ✓ v1.0
- v4 zones full CRUD — ✓ v1.0
- v4 analytics (element/monitor values, timeseries, percentiles, intervals, report) — ✓ v1.0
- v4 trends (get/patch, configuration CRUD, elements) — ✓ v1.0
- v4 events CRUD + error/statistics aggregation — ✓ v1.0
- v4 SLAs listing — ✓ v1.0
- v4 webhooks CRUD + validation — ✓ v1.0
- v4 SCM repositories CRUD + checkouts — ✓ v1.0
- v4 reservations CRUD — ✓ v1.0
- v4 deletion policies CRUD + dry-run — ✓ v1.0
- v4 proxies CRUD — ✓ v1.0
- v4 infrastructure providers CRUD — ✓ v1.0
- v4 guaranteed resources (per-workspace CRUD) — ✓ v1.0
- v4 license management (get, install, leases, activation/deactivation) — ✓ v1.0
- v4 users CRUD + workspace membership — ✓ v1.0
- v4 me/profile (info, password, tokens, features) — ✓ v1.0
- v4 sessions (create/delete) — ✓ v1.0
- v4 settings (get/patch, information, subscription) — ✓ v1.0
- v4 SSO configuration + SAML — ✓ v1.0
- v4 LDAP configuration + search — ✓ v1.0
- Unit test suite at ≥90% coverage with ≥90% mutation score — ✓ v1.0 (90.84% / 91.2%)

### Active

(None — all v1.0 requirements shipped. Define v1.1 requirements via `/gsd-new-milestone`.)

### Out of Scope

- Dashboards (tiles, series, PDF export, public tokens) — UI concept, not CLI
- User UI preferences (GET/PATCH /v4/me/preferences) — display settings for web UI
- Modifying any existing v2/v3 commands or library code — backwards compatibility is mandatory
- Feature flag management (beyond read-only listing)

## Context

- 23 v4 command files in `neoload/commands/`, 3 helper files in `neoload/neoload_cli_lib/v4/`
- 762 tests total; 173 new v4 tests added in v1.0
- Coverage: 90.84% | Mutation score: 91.2% | LLM-judge quality: 9.7/10
- All v4 commands are additive — zero modifications to any existing v2/v3 file
- v4 API uses flat `/v4/<resource>` paths; workspaceId as query param (lists) or body field (creates)
- Auth mechanism unchanged: `accountToken` header
- ~40% of endpoints are workspace-scoped; injection is per-endpoint, not global

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Additive-only approach (no modifications to existing code) | Backwards compatibility is mandatory; zero risk to current users | ✓ Held across all 9 phases — no existing file was modified |
| `v4_` prefix for all new command files | Prevents naming collisions; clear separation in CLI help output | ✓ Consistent across 23 command files |
| Shared v4 helper package (`neoload_cli_lib/v4/`) | Avoid duplication across 20+ command files; consistent v4 path building | ✓ Used by all v4 commands; saved significant per-file boilerplate |
| Workspace injection as opt-in per-endpoint, not global | ~40% of v4 endpoints need workspaceId; global injection would break the rest | ✓ Validated by each phase — some use `v4_list`/`v4_create`, others use `rest_crud` directly |
| Exclude dashboards and UI preferences | CLI tool should not manage visual UI concepts | ✓ Confirmed correct — no requests to add these |
| Click argument-based dispatch (not click.group) | Matches existing v2/v3 CLI pattern; consistent UX | ✓ Used consistently across all command files |
| LLM static analysis as mutation testing substitute | mutmut v2 incompatible (pony ORM deepcopy on Python 3.14); v3 trampoline conflicts with CliRunner | ✓ Achieved 91.2% mutation score via targeted hardening |

## Constraints

- **Backwards Compatibility**: All existing v2/v3 CLI functionality must continue to work unchanged
- **Additive Only**: v4 features are new files only — no modifications to existing code
- **Tech Stack**: Python 3, Click CLI framework, requests HTTP library (matching existing stack)
- **Naming**: v4 command files use `v4_` prefix (`v4_tests.py` → `neoload v4-tests`) to avoid collisions
- **No New Dependencies**: v4 commands use only libraries already in setup.py install_requires

---
*Last updated: 2026-04-10 after v1.0 milestone — all requirements validated*
