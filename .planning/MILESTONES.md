# Milestones

## v1.0 Full v4 API Coverage (Shipped: 2026-04-10)

**Phases:** 9 | **Plans:** 14 | **New command files:** 23 | **New tests:** 762 (173 v4-specific)  
**Coverage:** 90.84% | **Mutation score:** 91.2% | **LLM-judge quality:** 9.7/10

**Key accomplishments:**

- Built shared v4 helper package (`v4_endpoints.py`, `v4_client.py`) — variadic path builder, workspace injection helpers, auto-pagination, full CRUD wrappers — 28 unit tests
- Delivered 5 core resource commands (v4-tests, v4-results, v4-test-executions, v4-workspaces, v4-zones) covering the primary CI/CD test execution workflow
- Added analytics and trends (17 subcommands) and events/SLAs (9 subcommands) — all result-scoped
- Built operations layer: webhooks, SCM repositories, reservations, deletion policies — 26 subcommands
- Added infrastructure commands: proxies, infrastructure providers, guaranteed resources — 12 subcommands
- Implemented license management with 9 subcommands including activation/deactivation lifecycle
- Delivered users & identity: 6 files covering users, me, sessions, settings, SSO (SAML), LDAP — 41 subcommands
- Comprehensive test suite at 90.84% coverage with 91.2% mutation score — zero modifications to existing v2/v3 code

**Architecture decisions that held:**

- Additive-only approach — zero modifications to any existing file across all 9 phases
- `v4_` prefix for all command files — clean separation in CLI help output
- Shared `neoload_cli_lib/v4/` helper package — consistent path building across 23 command files
- Workspace injection per-endpoint (not global) — correctly handles ~40% of endpoints that are workspace-scoped

---
