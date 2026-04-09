# NeoLoad CLI — v4 API Expansion

## What This Is

A Python CLI tool (`neoload`) for automating NeoLoad Web operations — test management, execution, results analysis, and infrastructure configuration. Built with Click, it communicates with NeoLoad Web's REST API and is used in CI/CD pipelines and by performance engineers from the command line.

## Core Value

Provide complete CLI coverage of the NeoLoad Web v4 API so that every server-side operation available via the API can be performed from the command line or automated in scripts.

## Requirements

### Validated

- v2/v3 API coverage: login, test-settings CRUD, test-results CRUD, run/wait/stop, project upload, zones listing, workspaces ls/use, logs, report generation, as-code validation, fastfail SLA monitoring, Docker helpers, config management
- v4 API helper layer (v4_endpoints.py, v4_client.py) — additive, no changes to existing code — Validated in Phase 01: v4-foundation

### Active

- [ ] v4 tests CRUD + scenarios
- [ ] v4 results CRUD + sub-resources (contexts, elements, monitors, statistics, timeseries)
- [ ] v4 test-executions (create, get, cancel, force-cancel, logs)
- [ ] v4 workspaces full CRUD + members management
- [ ] v4 zones full CRUD
- [ ] v4 analytics (element/monitor values, timeseries, percentiles, intervals, report)
- [ ] v4 trends (get/patch, configuration CRUD, elements)
- [ ] v4 events CRUD + error/statistics aggregation
- [ ] v4 SLAs listing
- [ ] v4 webhooks CRUD + validation
- [ ] v4 SCM repositories CRUD + checkouts
- [ ] v4 reservations CRUD
- [ ] v4 deletion policies CRUD + dry-run
- [ ] v4 proxies CRUD
- [ ] v4 infrastructure providers CRUD
- [ ] v4 guaranteed resources (per-workspace CRUD)
- [ ] v4 license management (get, install, leases, activation/deactivation)
- [ ] v4 users CRUD + workspace membership
- [ ] v4 me/profile (info, password, tokens, features)
- [ ] v4 sessions (create/delete)
- [ ] v4 settings (get/patch, information, subscription)
- [ ] v4 SSO configuration + SAML
- [ ] v4 LDAP configuration + search

### Out of Scope

- Dashboards (tiles, series, PDF export, public tokens) — UI concept, not CLI
- User UI preferences (GET/PATCH /v4/me/preferences) — display settings for web UI
- Modifying any existing v2/v3 commands or library code — backwards compatibility is mandatory
- Feature flag management (beyond read-only listing)

## Context

- Existing CLI uses v2/v3 API endpoints with workspace-as-path-prefix pattern
- v4 API uses flat `/v4/<resource>` paths with workspaceId as query parameter (lists) or body field (creates)
- v4 test execution uses `POST /v4/test-executions` with structured JSON body (replaces query-string start endpoint)
- Auth mechanism unchanged: `accountToken` header
- ~177 v4 API operations total; ~150 are CLI-relevant after excluding UI concepts
- v4 OpenAPI specs are modular (per-service YAML files merged at runtime)
- The v4 API source lives at `/Users/m.zimmerman/projects/neoload`

## Constraints

- **Backwards Compatibility**: All existing v2/v3 CLI functionality must continue to work unchanged
- **Additive Only**: v4 features are new files only — no modifications to existing code
- **Tech Stack**: Python 3, Click CLI framework, requests HTTP library (matching existing stack)
- **Naming**: v4 command files use `v4_` prefix (`v4_tests.py` → `neoload v4-tests`) to avoid collisions
- **No New Dependencies**: v4 commands use only libraries already in setup.py install_requires

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Additive-only approach (no modifications to existing code) | Backwards compatibility is mandatory; zero risk to current users | — Pending |
| v4_ prefix for all new command files | Prevents naming collisions; clear separation in CLI help output | — Pending |
| Shared v4 helper package (neoload_cli_lib/v4/) | Avoid duplication across 20+ command files; consistent v4 path building | — Pending |
| Workspace injection as opt-in, not global | v4 API only requires workspaceId on specific list/create endpoints | — Pending |
| Exclude dashboards and UI preferences | CLI tool should not manage visual UI concepts | — Pending |

---
*Last updated: 2026-04-09 after initial planning*
