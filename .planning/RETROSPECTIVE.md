# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

---

## Milestone: v1.0 — Full v4 API Coverage

**Shipped:** 2026-04-10  
**Phases:** 9 | **Plans:** 14 | **Command files delivered:** 23  
**Tests:** 762 total (173 new v4) | **Coverage:** 90.84% | **Mutation score:** 91.2%

### What Was Built

- Shared v4 helper package — variadic path builder, workspace injection, auto-pagination, full CRUD wrappers
- 23 v4 command files covering ~150 subcommands across all major NeoLoad Web API domains
- Core CI/CD commands: v4-tests, v4-results, v4-test-executions with --wait polling (exit 1 on failure)
- Analytics, trends, events, SLAs — all result-scoped, no workspace injection needed
- Operations layer: webhooks, SCM repositories, reservations, deletion policies
- Infrastructure: proxies, infrastructure providers, guaranteed resources (workspace-as-path-param pattern)
- License management lifecycle: get, install, leases, activation/deactivation, forced-release
- Users & identity: users, me, sessions, settings, SSO (SAML), LDAP — 41 subcommands in 6 files
- Full unit test suite via testing-agent skill — LLM-as-judge score 9.7/10

### What Worked

- **Additive-only discipline held perfectly** — zero modifications to any existing file across all 9 phases. The constraint that seemed restrictive turned out to be easy to honor because v4 paths are entirely separate.
- **Shared helper package** — `v4_endpoints.py` + `v4_client.py` paid off immediately. Every subsequent command file was faster to write with consistent path building and workspace injection.
- **Click argument dispatch (not click.group)** — matching the existing v2/v3 pattern made each command file consistent with the rest of the codebase. No design decisions at the command level.
- **Per-endpoint workspace injection** — deciding early that injection is opt-in (not global) prevented a class of bugs. Each phase confirmed the right subset of endpoints needed it.
- **testing-agent skill** — running the full quality audit (coverage → mutation analysis → LLM-judge) in one structured workflow surfaced gaps and scored objectively. Achieved 9.7/10.
- **Parallel sub-agents for test generation** — 5 parallel agents generating tests for 20+ low-coverage modules reduced test-writing time significantly.

### What Was Inefficient

- **mutmut incompatibility not discovered until Phase 9** — both v2 and v3 fail on Python 3.14 (pony ORM deepcopy / trampoline env var conflicts with CliRunner). Earlier discovery would have allowed planning LLM static analysis from the start.
- **Plan 01-01 superseded before execution** — the first plan was written before CONTEXT.md decisions were finalized, requiring a full rewrite as 01-02. Front-loading context gathering (discuss-phase) before planning would have avoided this.
- **Branch reorganization as a separate task** — all phase commits landed on one branch during execution; reorganizing into 9 per-phase branches at the end required manual effort. Future: start each phase on its own branch from the beginning (per CLAUDE.md convention).
- **SUMMARY.md one-liner format inconsistency** — some SUMMARY files used `One-liner:` field, others used `## One-liner` headers, others had neither. Made automated extraction unreliable (MILESTONES.md auto-content needed manual fixing).

### Patterns Established

- **`v4_` prefix + `neoload_cli_lib/v4/`** — the naming and location convention for all v4 work. Proven across 23 files.
- **Click argument dispatch for v4 commands** — `@click.command()` with `click.Choice` argument, not `@click.group()`. Matches existing CLI patterns.
- **`rest_crud` direct for non-workspace-scoped endpoints** — when `v4_client` helpers would inject unwanted workspaceId, drop down to `rest_crud` directly. This is the right escape hatch, not a code smell.
- **LLM static mutation analysis as mutmut substitute on Python 3.14** — select 4-5 core files, generate mutant candidates, identify survivors, harden assertions. Achieves comparable confidence to automated mutation testing.
- **testing-agent skill for quality verification** — full pipeline: fix errors → boost coverage → mutation analysis → LLM-as-judge scoring. Reusable for future milestones.

### Key Lessons

1. **Finalize CONTEXT.md before writing any PLAN.md** — the 01-01 supersession cost was low, but the lesson is clear: discuss-phase should always precede plan-phase for non-trivial phases.
2. **Branch per phase from the start** — CLAUDE.md already says this, but it wasn't followed during execution. The end-of-milestone branch reorganization worked, but it's cleaner to create branches upfront.
3. **Test for exact URL paths, not just HTTP method** — the mutation hardening step showed that wildcard URL mocks (`mock_get`) pass even with wrong paths. Assert the full URL in every test.
4. **Python version compatibility matters for tooling** — check mutmut/coverage tool compatibility before planning the test phase. LLM static analysis is a viable substitute but should be planned, not improvised.
5. **Per-phase SUMMARY one-liner should be a consistent field** — YAML frontmatter `one_liner:` field enables reliable extraction. Freeform markdown headers don't.

---

## Cross-Milestone Trends

### Cumulative Quality

| Milestone | Tests | Coverage | Mutation Score | Command Files |
|-----------|-------|----------|----------------|---------------|
| v1.0 | 762 | 90.84% | 91.2% | 23 new v4 |

### Top Lessons (Verified Across Milestones)

1. Additive-only constraints are easier to honor than expected when the API surface is fully separate
2. Shared helper packages pay off immediately — invest in them at Phase 1, not Phase 3
3. Context gathering before planning prevents plan rewrites
