# Phase 09: Test Coverage - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning
**Mode:** Auto-generated (smart discuss — plan pre-exists, established pattern)

<domain>
## Phase Boundary

Unit tests for the 18 v4 command modules introduced in phases 3–8. Helper tests (test_v4_endpoints.py, test_v4_client.py) already exist from Phase 1. Command tests for Phase 2 (tests, results, test-executions, workspaces, zones) already exist from Phase 2.

New test files needed (18): test_v4_analytics, test_v4_trends, test_v4_events, test_v4_slas, test_v4_webhooks, test_v4_scm_repositories, test_v4_reservations, test_v4_deletion_policies, test_v4_proxies, test_v4_infrastructure_providers, test_v4_guaranteed_resources, test_v4_license, test_v4_users, test_v4_me, test_v4_sessions, test_v4_settings, test_v4_sso, test_v4_ldap

</domain>

<decisions>
## Implementation Decisions

### Test pattern (follow tests/commands/test_v4_tests.py exactly)
- Use `CliRunner` from `click.testing`
- Mock `rest_crud` functions via `monkeypatch`
- Use `@pytest.mark.usefixtures("neoload_login")` on each class
- `_mock_workspace` helper for workspace-aware commands
- Test: missing/required args, successful invocation (exit_code == 0), correct output

### Workspace-aware commands (mock workspace where needed)
- `v4_webhooks`: ls/create need workspace mock
- `v4_reservations`: ls/create need workspace mock
- `v4_deletion_policies`: ls/create/dry-run need workspace mock
- `v4_guaranteed_resources`: all subcommands need workspace mock (path param)
- `v4_license leases-create`: needs workspace mock

### Confirmed
- No modifications to any existing test files
- New files in tests/commands/ only

</decisions>

<code_context>
## Existing Code Insights

Reference: tests/commands/test_v4_tests.py — clean example of the full pattern.
The conftest.py provides `neoload_login` fixture.

</code_context>

<specifics>
## Specific Requirements

18 test files, each covering all subcommands. Run `python -m pytest tests/` to validate.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
