# Phase 01: v4 API Foundation - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Create `neoload/neoload_cli_lib/v4/` — a new sub-package containing path-building helpers and thin HTTP client wrappers. This is the shared foundation all v4 command files will import. No v4 commands are implemented in this phase. No existing files are modified.

</domain>

<decisions>
## Implementation Decisions

### Additive-only constraint
- **D-01:** Zero modifications to any existing file — no changes to `rest_crud.py`, `user_data.py`, any existing command, or any existing test
- **D-02:** New files only: `neoload/neoload_cli_lib/v4/__init__.py`, `v4_endpoints.py`, `v4_client.py`, and their tests

### workspaceId is mandatory
- **D-03:** workspaceId is MANDATORY for all v4 workspace-scoped operations — same contract as v3, not opt-in. The v4 helper layer auto-injects workspaceId; callers do not pass it manually.
- **D-04:** `v4_workspace_params()` raises `CliException` if no workspace stored. `v4_inject_workspace(data)` raises `CliException` if no workspace stored. No soft/optional variant.
- **D-05:** Non-workspace endpoints (license, me, settings, sessions, SSO, LDAP) are NOT passed through `v4_list`/`v4_create` — those future commands will call `rest_crud` directly with `v4_endpoint()` paths. The workspace-aware helpers are only for workspace-scoped resources.

### v4_endpoint — variadic path builder
- **D-06:** `v4_endpoint(*segments)` accepts any number of path segments and joins them: `v4_endpoint('tests')` → `'v4/tests'`, `v4_endpoint('tests', test_id)` → `'v4/tests/{id}'`, `v4_endpoint('tests', test_id, 'scenarios')` → `'v4/tests/{id}/scenarios'`, `v4_endpoint('tests', test_id, 'scenarios', scenario_id)` → `'v4/tests/{id}/scenarios/{id}'`. Segments are joined with `/` after the `v4/` prefix.
- **D-07:** `v4_base()` helper returns the literal string `'v4'` (for cases needing just the prefix)

### v4_list — auto-paginating list
- **D-08:** `v4_list(*path_segments, params=None)` auto-paginates using v4's `pageNumber/pageSize` model (NOT `limit/offset`). Page size default: 200 (v4 API max). Loops until all pages fetched.
- **D-09:** v4 list responses return `{"items": [...], "total": N, "pageNumber": N, "pageSize": N}` envelopes. `v4_list` unwraps the `items` array and returns a flat Python list — same shape as what `rest_crud.get_with_pagination` returns for v2/v3.
- **D-10:** workspaceId auto-injected as query param: `?workspaceId={id}&pageNumber=N&pageSize=200`. Callers may pass additional filter params via `params` kwarg.

### v4_client — thin HTTP wrappers
- **D-11:** `v4_create(*path_segments, data)` — POSTs to `v4_endpoint(*path_segments)`. Calls `v4_inject_workspace(data)` to add workspaceId to body before posting. Returns `response.json()`.
- **D-12:** `v4_get(*path_segments)` — GETs single resource. No workspace injection (workspace not needed for by-ID lookups). Returns `response.json()`.
- **D-13:** `v4_update(*path_segments, data)` — PATCHes resource. No workspace injection (workspace not needed for by-ID updates). Returns `response.json()`.
- **D-14:** `v4_replace(*path_segments, data)` — PUTs resource. No workspace injection. Returns `response.json()`.
- **D-15:** `v4_delete(*path_segments)` — DELETEs resource. No workspace injection. Returns `response.json()` (or None if 204 No Content).
- **D-16:** All functions delegate entirely to `rest_crud` for HTTP, auth, retries, and error handling. No new HTTP logic.

### Return values
- **D-17:** All client functions return the full `response.json()` dict — same as `rest_crud` does today. Commands extract what they need and print via `tools.print_json()`.

### Claude's Discretion
- Exact Python kwarg syntax for variadic path segments (positional *args vs named params)
- How to handle `v4_delete` returning 202/204 with empty body (return None or `{}`)
- Internal pagination loop implementation details (while loop vs recursion)
- Test fixture setup (use existing `neoload_login` fixture from conftest.py)

</decisions>

<specifics>
## Specific Ideas

- The workspace injection model mirrors v3: just as `base_endpoint_with_workspace()` always injects the workspace into the v3 path, `v4_list` and `v4_create` always inject workspaceId — no command should have to think about it.
- `v4_endpoint` variadic design is intentional: enables Phase 2+ to call `v4_endpoint('tests', id, 'scenarios')` rather than doing `v4_endpoint('tests', id) + '/scenarios'` string manipulation.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### v4 API pagination and response shape
- `/Users/m.zimmerman/projects/neoload/nlweb-api-router/verticle/src/test/resources/com/neotys/nlweb/api/router/v4/swaggerMerged.yaml` — v4 OpenAPI spec with `SomePage` schema (canonical `{items, total, pageNumber, pageSize}` response envelope) and `pageNumber/pageSize` query params

### v4 API service specs (actual endpoints)
- `/Users/m.zimmerman/projects/neoload/nlweb-resources-reservation/rest/src/main/resources/nlweb-resources-reservation-rest.yaml` — reservations, license, guaranteed-resources v4 endpoints
- `/Users/m.zimmerman/projects/neoload/nlweb-bench-runtime/rest/src/main/resources/nlweb-bench-runtime-rest.yaml` — test-executions and results/logs v4 endpoints

### Existing CLI lib to wrap
- `neoload/neoload_cli_lib/rest_crud.py` — `get`, `post`, `put`, `patch`, `delete`, `get_with_pagination` signatures; all v4 client functions MUST delegate to these, not replicate HTTP logic
- `neoload/neoload_cli_lib/user_data.py` — `get_meta('workspace id')` for workspace retrieval; `get_meta` returns None if not set
- `neoload/neoload_cli_lib/cli_exception.py` — `CliException` for all user-facing errors

### Test patterns
- `tests/neoload_cli_lib/test_rest_crud.py` — `monkeypatch.setattr(rest_crud, method, lambda ...)` pattern used throughout; v4 tests should follow the same approach
- `tests/helpers/test_utils.py` — `mock_api_get`, `mock_api_post`, `mock_api_patch`, `mock_api_delete_raw` helpers; new `mock_api_*` helpers for v4 may be added here if useful
- `tests/conftest.py` — `neoload_login` fixture setup; v4 tests should use `@pytest.mark.usefixtures("neoload_login")`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `rest_crud.get_with_pagination` — NOT reusable for v4 (uses limit/offset, expects flat list response). v4_list must implement its own pageNumber/pageSize loop.
- `rest_crud.get/post/put/patch/delete` — directly reusable; v4_client wraps these with v4 path building
- `user_data.get_meta('workspace id')` — returns stored workspace ID or None; used by `v4_workspace_params()` and `v4_inject_workspace()`
- `CliException` — reuse for all error conditions (missing workspace, etc.)

### Established Patterns
- Module-level private state: acceptable for workspace caching if needed, but `user_data.get_meta` already handles this
- `cli_exception.CliException` raised for all user-facing errors — v4 helpers follow the same convention
- `monkeypatch.setattr(rest_crud, method, lambda ...)` for tests — v4 tests follow this pattern exactly
- No explicit `__all__`; all public functions are implicitly exported

### Integration Points
- `neoload/neoload_cli_lib/v4/__init__.py` is a package marker only — no code
- v4 command files (Phase 2+) will import: `from neoload_cli_lib.v4 import v4_client, v4_endpoints`
- No changes to `neoload/__main__.py` or any existing command registration

</code_context>

<deferred>
## Deferred Ideas

- `v4_list` with explicit page control (for streaming/large datasets) — not needed now; all ls commands fetch everything
- `v4_try_workspace_params()` soft variant returning `{}` if no workspace — rejected; workspace is mandatory for v4 workspace-scoped ops
- v4 name resolver (Resolver equivalent for v4) — deferred to Phase 2+ where it's needed per-resource

</deferred>

---

*Phase: 01-v4-foundation*
*Context gathered: 2026-04-09*
