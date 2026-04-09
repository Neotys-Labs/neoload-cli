# Phase 01: v4 API Foundation - Research

**Researched:** 2026-04-09
**Domain:** Python CLI library module — new sub-package wrapping existing `rest_crud.py` for v4 API paths and pagination
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Zero modifications to any existing file — no changes to `rest_crud.py`, `user_data.py`, any existing command, or any existing test
- **D-02:** New files only: `neoload/neoload_cli_lib/v4/__init__.py`, `v4_endpoints.py`, `v4_client.py`, and their tests
- **D-03:** workspaceId is MANDATORY for all v4 workspace-scoped operations — same contract as v3, not opt-in. The v4 helper layer auto-injects workspaceId; callers do not pass it manually.
- **D-04:** `v4_workspace_params()` raises `CliException` if no workspace stored. `v4_inject_workspace(data)` raises `CliException` if no workspace stored. No soft/optional variant.
- **D-05:** Non-workspace endpoints (license, me, settings, sessions, SSO, LDAP) are NOT passed through `v4_list`/`v4_create` — those future commands will call `rest_crud` directly with `v4_endpoint()` paths.
- **D-06:** `v4_endpoint(*segments)` accepts any number of path segments and joins them: `v4_endpoint('tests')` → `'v4/tests'`, `v4_endpoint('tests', id)` → `'v4/tests/{id}'`, `v4_endpoint('tests', id, 'scenarios')` → `'v4/tests/{id}/scenarios'`. Segments are joined with `/` after the `v4/` prefix.
- **D-07:** `v4_base()` helper returns the literal string `'v4'`
- **D-08:** `v4_list(*path_segments, params=None)` auto-paginates using v4's `pageNumber/pageSize` model (NOT `limit/offset`). Page size default: 200 (v4 API max). Loops until all pages fetched.
- **D-09:** v4 list responses return `{"items": [...], "total": N, "pageNumber": N, "pageSize": N}` envelopes. `v4_list` unwraps the `items` array and returns a flat Python list — same shape as `rest_crud.get_with_pagination` returns for v2/v3.
- **D-10:** workspaceId auto-injected as query param: `?workspaceId={id}&pageNumber=N&pageSize=200`. Callers may pass additional filter params via `params` kwarg.
- **D-11:** `v4_create(*path_segments, data)` — POSTs to `v4_endpoint(*path_segments)`. Calls `v4_inject_workspace(data)` to add workspaceId to body before posting. Returns `response.json()`.
- **D-12:** `v4_get(*path_segments)` — GETs single resource. No workspace injection. Returns `response.json()`.
- **D-13:** `v4_update(*path_segments, data)` — PATCHes resource. No workspace injection. Returns `response.json()`.
- **D-14:** `v4_replace(*path_segments, data)` — PUTs resource. No workspace injection. Returns `response.json()`.
- **D-15:** `v4_delete(*path_segments)` — DELETEs resource. No workspace injection. Returns `response.json()` (or None if 204 No Content).
- **D-16:** All functions delegate entirely to `rest_crud` for HTTP, auth, retries, and error handling. No new HTTP logic.
- **D-17:** All client functions return the full `response.json()` dict — same as `rest_crud` does today.

### Claude's Discretion

- Exact Python kwarg syntax for variadic path segments (positional *args vs named params)
- How to handle `v4_delete` returning 202/204 with empty body (return None or `{}`)
- Internal pagination loop implementation details (while loop vs recursion)
- Test fixture setup (use existing `neoload_login` fixture from conftest.py)

### Deferred Ideas (OUT OF SCOPE)

- `v4_list` with explicit page control (for streaming/large datasets)
- `v4_try_workspace_params()` soft variant returning `{}` if no workspace — rejected
- v4 name resolver (Resolver equivalent for v4) — deferred to Phase 2+
</user_constraints>

---

## Summary

Phase 01 creates a new Python sub-package at `neoload/neoload_cli_lib/v4/` with two modules: `v4_endpoints.py` (path construction + workspace injection helpers) and `v4_client.py` (thin HTTP wrappers over `rest_crud`). No existing files are touched.

The key insight is that `rest_crud.get_with_pagination` uses `limit/offset` and returns a flat list directly from the response. It cannot be reused for v4. `v4_list` must implement its own `pageNumber/pageSize` loop and unwrap `response['items']` from each page envelope before accumulating. The termination condition is `len(accumulated) >= response['total']` — the `total` field from `SomePage` is the canonical signal (required field in the v4 schema).

`rest_crud.delete` returns a raw `Response` object (not `.json()`). `v4_delete` must handle the case where the body is empty (HTTP 202, no content) and return `None` or `{}` per Claude's discretion.

**Primary recommendation:** Implement both modules in a single wave. No dependencies on other phases. Tests use `monkeypatch.setattr(rest_crud, method, lambda ...)` exactly as `test_rest_crud.py` does — no new test infrastructure required.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `neoload_cli_lib.rest_crud` | (project-internal) | All HTTP calls: get, post, put, patch, delete | Existing abstraction; handles auth, retries, error handling — must not be duplicated |
| `neoload_cli_lib.user_data` | (project-internal) | `get_meta('workspace id')` → workspace ID or None | Single source of truth for stored config |
| `neoload_cli_lib.cli_exception` | (project-internal) | `CliException` for all user-facing errors | Project-wide convention |
| `pytest` | 9.0.2 | Test framework | Already installed; `python3 -m pytest` is the run command |

[VERIFIED: codebase grep + `python3 -m pytest --version`]

### No New Dependencies

Zero new packages to install. All imports are from the existing project library.

---

## Architecture Patterns

### Package Structure

```
neoload/
  neoload_cli_lib/
    v4/
      __init__.py          # empty package marker
      v4_endpoints.py      # path builder + workspace helpers
      v4_client.py         # HTTP wrappers delegating to rest_crud

tests/
  neoload_cli_lib/
    v4/                    # NEW — no __init__.py needed (pytest discovers without it)
      test_v4_endpoints.py
      test_v4_client.py
```

**Note on `__init__.py` in tests:** `tests/neoload_cli_lib/` has NO `__init__.py` today, and neither do `tests/commands/` or `tests/commands/workspaces/`. Only `tests/`, `tests/helpers/`, and `tests/resources/` have them. The pattern is: test subdirectories do NOT need `__init__.py`. The new `tests/neoload_cli_lib/v4/` directory follows that same convention — no `__init__.py` needed. [VERIFIED: `find tests -name "__init__.py"`]

### Pattern 1: v4_endpoints.py — Path Builder + Workspace Helpers

```python
# Source: CONTEXT.md D-06, D-07, D-03, D-04
from neoload_cli_lib import user_data, cli_exception

def v4_base():
    return 'v4'

def v4_endpoint(*segments):
    """Join any number of path segments after 'v4/'."""
    return 'v4/' + '/'.join(str(s) for s in segments)

def v4_workspace_params():
    """Return {'workspaceId': id} dict. Raises CliException if no workspace stored."""
    workspace_id = user_data.get_meta('workspace id')
    if workspace_id is None:
        raise cli_exception.CliException(
            "No workspace set. Please use 'neoload workspaces use <id>' first."
        )
    return {'workspaceId': workspace_id}

def v4_inject_workspace(data):
    """Return copy of data dict with workspaceId added. Raises CliException if no workspace stored."""
    workspace_id = user_data.get_meta('workspace id')
    if workspace_id is None:
        raise cli_exception.CliException(
            "No workspace set. Please use 'neoload workspaces use <id>' first."
        )
    result = dict(data)
    result['workspaceId'] = workspace_id
    return result
```

[VERIFIED: user_data.get_meta returns `None` when key not in metadata — confirmed in user_data.py line 210-213]

### Pattern 2: v4_client.py — v4_list with pageNumber/pageSize Pagination

The v4 `SomePage` schema [VERIFIED: swaggerMerged.yaml lines 708-733] has:
- `items` (required array) — the entities for this page
- `total` (required int64) — total count across ALL pages
- `pageNumber` (int32, default 0) — 0-indexed
- `pageSize` (int32, max 200)

The termination condition is `len(all_items) >= total`. This is reliable because `total` is a required field.

```python
# Source: CONTEXT.md D-08, D-09, D-10 + swaggerMerged.yaml SomePage schema
from neoload_cli_lib import rest_crud
from neoload_cli_lib.v4 import v4_endpoints

def v4_list(*path_segments, params=None):
    """Auto-paginating list for workspace-scoped v4 resources. Returns flat list."""
    endpoint = v4_endpoints.v4_endpoint(*path_segments)
    workspace_params = v4_endpoints.v4_workspace_params()  # raises if no workspace

    page_number = 0
    page_size = 200
    all_items = []

    while True:
        query_params = {**workspace_params, 'pageNumber': page_number, 'pageSize': page_size}
        if params:
            query_params.update(params)
        response = rest_crud.get(endpoint, query_params)
        items = response.get('items', [])
        all_items.extend(items)
        total = response.get('total', 0)
        if len(all_items) >= total or not items:
            break
        page_number += 1

    return all_items
```

### Pattern 3: v4_client.py — Other HTTP Wrappers

```python
# Source: CONTEXT.md D-11 through D-17
def v4_get(*path_segments):
    return rest_crud.get(v4_endpoints.v4_endpoint(*path_segments))

def v4_create(*path_segments, data):
    injected = v4_endpoints.v4_inject_workspace(data)  # raises if no workspace
    return rest_crud.post(v4_endpoints.v4_endpoint(*path_segments), injected)

def v4_update(*path_segments, data):
    return rest_crud.patch(v4_endpoints.v4_endpoint(*path_segments), data)

def v4_replace(*path_segments, data):
    return rest_crud.put(v4_endpoints.v4_endpoint(*path_segments), data)

def v4_delete(*path_segments):
    response = rest_crud.delete(v4_endpoints.v4_endpoint(*path_segments))
    # rest_crud.delete returns raw Response object (not .json())
    if response.status_code == 204 or not response.content:
        return None
    return response.json()
```

**Critical:** `rest_crud.delete` returns a raw `requests.Response` object, NOT `.json()`. [VERIFIED: rest_crud.py line 160-164] All other `rest_crud` methods (get, post, put, patch) return `.json()` already. `v4_delete` is the only wrapper that needs to call `.json()` itself.

### Pattern 4: Test Structure — monkeypatch.setattr

All v4 tests follow the existing pattern from `test_rest_crud.py` and `test_utils.py`:

```python
# Source: tests/neoload_cli_lib/test_rest_crud.py + tests/helpers/test_utils.py
import pytest
from neoload_cli_lib.v4 import v4_client, v4_endpoints
from neoload_cli_lib import rest_crud, user_data

@pytest.mark.usefixtures("neoload_login")
class TestV4Client:
    def test_v4_list_single_page(self, monkeypatch, valid_data):
        monkeypatch.setattr(rest_crud, 'get',
            lambda endpoint, params: {
                'items': [{'id': '1', 'name': 'test'}],
                'total': 1,
                'pageNumber': 0,
                'pageSize': 200
            }
        )
        monkeypatch.setattr(user_data, 'get_meta',
            lambda key: valid_data.default_workspace_id if key == 'workspace id' else None
        )
        result = v4_client.v4_list('tests')
        assert len(result) == 1
        assert result[0]['id'] == '1'
```

**Key:** `user_data.get_meta` must also be monkeypatched in tests that exercise workspace-related paths, since `neoload_login` fixture (without `--workspace`) does not set a workspace.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP auth, retries, SSL | Custom requests Session | `rest_crud.get/post/put/patch/delete` | Already handles 429 retry, accountToken header, SSL certs |
| Error handling for 4xx/5xx | Custom status checking | `rest_crud.__handle_error` (called inside all rest_crud methods) | Consistent CliException messages across all commands |
| URL construction | String concatenation | `rest_crud.__create_url` (called internally) | User's configured base URL is already applied |
| Workspace lookup | Read from config file directly | `user_data.get_meta('workspace id')` | Handles YAML parsing, singleton pattern, null coercion |

---

## Inconsistencies Between 01-01-PLAN.md and CONTEXT.md

The existing `01-01-PLAN.md` was written before CONTEXT.md was finalized. The following divergences must be resolved in the new plan:

| # | 01-01-PLAN.md says | CONTEXT.md says | Verdict |
|---|-------------------|-----------------|---------|
| I-1 | `must_haves.truths`: "Workspace injection is opt-in, not auto-injected" | D-03: "workspaceId is MANDATORY…auto-injected; callers do not pass it manually" | **PLAN IS WRONG.** CONTEXT.md wins. Workspace is mandatory and auto-injected by `v4_list` and `v4_create`. |
| I-2 | `v4_endpoint(resource, resource_id=None)` — only 2 fixed args | D-06: `v4_endpoint(*segments)` — variadic, unlimited segments | **PLAN IS WRONG.** Must be variadic to support `v4_endpoint('tests', id, 'scenarios')`. |
| I-3 | `v4_list(resource, params=None)` — named `resource` arg | D-08: `v4_list(*path_segments, params=None)` — variadic path segments | **PLAN IS WRONG.** Must be variadic to match `v4_endpoint` signature. |
| I-4 | `v4_create(resource, data)` — caller "injects workspace into data if needed" | D-11: `v4_create(*path_segments, data)` — auto-injects workspace into body | **PLAN IS WRONG.** Auto-injection is mandatory, not caller-optional. |
| I-5 | `v4_list` described as using `get_with_pagination` implicitly | CONTEXT.md code_context: "rest_crud.get_with_pagination — NOT reusable for v4 (uses limit/offset)" | **PLAN IS WRONG.** Must implement own pageNumber/pageSize loop. |
| I-6 | `v4_get(resource, resource_id)` — 2 fixed args | D-12: `v4_get(*path_segments)` — variadic | **PLAN IS WRONG.** All client functions take variadic path segments. |
| I-7 | `v4_update(resource, resource_id, data)` — 3 fixed args | D-13: `v4_update(*path_segments, data)` — variadic | **PLAN IS WRONG.** Same pattern. |
| I-8 | `v4_replace(resource, resource_id, data)` — 3 fixed args | D-14: `v4_replace(*path_segments, data)` — variadic | **PLAN IS WRONG.** Same pattern. |
| I-9 | `v4_delete(resource, resource_id)` — 2 fixed args | D-15: `v4_delete(*path_segments)` — variadic | **PLAN IS WRONG.** Same pattern. |
| I-10 | STATE.md says "workspaceId is opt-in per command, not globally injected" | D-03 in CONTEXT.md: workspaceId is MANDATORY | **STATE.md IS STALE.** CONTEXT.md is authoritative — STATE.md was written before the discussion phase and must not be used as a decision source. |

**Summary:** The existing 01-01-PLAN.md gets the file structure right (correct paths, additive-only constraint, test locations) but gets almost all function signatures wrong and has the wrong workspace model. The new plan must supersede it entirely for task specifications.

---

## Common Pitfalls

### Pitfall 1: Using rest_crud.get_with_pagination for v4

**What goes wrong:** Calls `rest_crud.get_with_pagination(endpoint, api_query_params=params)` which uses `limit/offset` query params. The v4 API ignores `limit/offset` and uses `pageNumber/pageSize`. Result: only the first 200 items are returned.

**Why it happens:** The helper name sounds generic. The CONTEXT.md explicitly warns against this.

**How to avoid:** `v4_list` must implement its own loop using `pageNumber` (0-indexed) and `pageSize`, reading `response['total']` to determine when to stop.

**Warning signs:** Tests pass with small datasets but production calls silently truncate at 200 items.

### Pitfall 2: rest_crud.delete returns Response, not dict

**What goes wrong:** Calling `rest_crud.delete(endpoint).json()` directly works for non-empty bodies but raises `json.decoder.JSONDecodeError` when the server returns HTTP 202 with an empty body (which is the v4 delete response per swaggerMerged.yaml).

**Why it happens:** All other `rest_crud` functions (`get`, `post`, `put`, `patch`) already call `.json()` internally and return a dict. `delete` is the exception — it returns the raw `Response`. [VERIFIED: rest_crud.py lines 160-164]

**How to avoid:** `v4_delete` must check `response.content` or `response.status_code` before calling `.json()`. Return `None` for empty/204 responses.

### Pitfall 3: Forgetting to mock user_data.get_meta in tests

**What goes wrong:** Tests that call `v4_list` or `v4_create` fail because `v4_workspace_params()` calls `user_data.get_meta('workspace id')` which returns `None` when no workspace is set via `--workspace` in conftest.

**Why it happens:** The `neoload_login` fixture invokes `login` but the default test workspace option is `None`. The `get_meta('workspace id')` call then raises `CliException("No workspace set…")` — which looks like a real error in test output.

**How to avoid:** Each test that exercises workspace-aware paths must `monkeypatch.setattr(user_data, 'get_meta', lambda key: '5e3acde2e860a132744ca916' if key == 'workspace id' else None)` — or use `valid_data.default_workspace_id`.

### Pitfall 4: Python *args with keyword-only data parameter

**What goes wrong:** `def v4_create(*path_segments, data)` — this syntax requires `data` to be passed as a keyword argument (`v4_create('tests', data={...})`). If callers use positional arguments, Python raises `TypeError`.

**Why it happens:** In Python 3, any parameter after `*args` is keyword-only. This is correct behavior and is what CONTEXT.md intends (D-11 says `data` is a keyword param).

**How to avoid:** Document that `data` must be passed as a keyword arg. Tests must use `v4_client.v4_create('tests', data={...})`.

### Pitfall 5: pageNumber is 0-indexed

**What goes wrong:** Starting `pageNumber` at 1 instead of 0 skips the first page. The v4 API uses 0-indexed pages (`default: 0` in the swagger spec).

**Why it happens:** Confusion with 1-indexed pagination patterns from other APIs.

**How to avoid:** Initialize `page_number = 0` in the pagination loop. [VERIFIED: swaggerMerged.yaml line 99 — `default: 0`, `minimum: 0`]

---

## Code Examples

### Exact rest_crud signatures (v4_client must delegate to these)

```python
# Source: neoload/neoload_cli_lib/rest_crud.py (verified lines 67-164)

def get_with_pagination(endpoint: str, page_size=200, api_query_params=None):
    # Uses limit/offset — NOT usable for v4
    ...

def get(endpoint: str, params=None):
    # Returns response.json() — a dict or list
    return __handle_error(get_raw(endpoint, params)).json()

def post(endpoint: str, data):
    # Returns response.json()
    ...
    return response.json()

def put(endpoint: str, data):
    # Returns response.json()
    ...
    return response.json()

def patch(endpoint: str, data):
    # Returns response.json()
    ...
    return response.json()

def delete(endpoint: str):
    # Returns raw requests.Response object (NOT .json())
    response = http.delete(...)
    __handle_error(response)
    return response    # <-- raw Response, caller must call .json() if needed
```

### user_data.get_meta return value

```python
# Source: neoload/neoload_cli_lib/user_data.py lines 209-213
def get_meta(key):
    result = get_user_data().metadata.get(key, None)
    if result == 'null':
        result = None
    return result
    # Returns None when key not in metadata OR when value is the string 'null'
    # Returns the stored string value otherwise (e.g., '5e3acde2e860a132744ca916')
```

### SomePage response envelope (from swaggerMerged.yaml)

```yaml
# Source: swaggerMerged.yaml lines 708-733
SomePage:
  required:
    - items    # array — ALWAYS present
    - total    # int64 — ALWAYS present — use for termination condition
  properties:
    items:      type: array
    total:      type: integer (int64) — total across ALL pages
    pageNumber: type: integer (int32, default: 0)
    pageSize:   type: integer (int32, max: 200, default: 25)
```

### v4 delete response (from swaggerMerged.yaml)

```yaml
# Source: swaggerMerged.yaml lines 26-63 (/v4/other-data/{id} DELETE)
responses:
  "202":
    description: The other data has been successfully deleted
    # No content schema — empty body
```

v4 DELETE returns HTTP 202 with empty body (not 204). `v4_delete` must handle this.

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| v2/v3: workspace in URL path (`v3/workspaces/{id}/tests`) | v4: workspace as query param (`v4/tests?workspaceId={id}`) or body field | `v4_endpoint` never embeds workspaceId in path — it belongs in params or body |
| v2/v3: `limit/offset` pagination | v4: `pageNumber/pageSize` (0-indexed) | Cannot reuse `rest_crud.get_with_pagination` |
| v2/v3: flat list response (`[{...}, {...}]`) | v4: page envelope (`{"items": [...], "total": N}`) | Must unwrap `items` to return same shape as v2/v3 list functions |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `v4_delete` should return `None` for empty 202 response | Code Examples | If v4 deletes actually return JSON body in some endpoints, callers would get `None` instead of data — low risk since delete callers rarely use the return value |
| A2 | `tests/neoload_cli_lib/v4/` directory does not need `__init__.py` for pytest discovery | Architecture Patterns | If pytest is configured with `rootdir` options that require it, tests would not be discovered — can be fixed by adding `__init__.py` if needed |

---

## Open Questions

1. **v4_delete: None vs {} for empty 202 body**
   - What we know: HTTP 202 with empty body is the spec response; `rest_crud.delete` returns raw Response; `response.content` would be empty bytes
   - What's unclear: Should `v4_delete` return `None` or `{}` — both are within Claude's Discretion (D-15)
   - Recommendation: Return `None` — more Pythonic; callers can check `if result is not None`

2. **pytest marker for v4 tests**
   - What we know: `pytest.ini` lists named markers (authentication, settings, results, workspaces, etc.); no `v4` marker exists
   - What's unclear: Should a `v4` marker be registered in `pytest.ini`, or skip markers entirely for v4 tests
   - Recommendation: Register `v4foundation: marks tests of the v4 helper package` in `pytest.ini` — however this would technically modify an existing file, which conflicts with D-01. Alternative: use no custom marker, just `@pytest.mark.usefixtures("neoload_login")`.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | All implementation | Yes | 3.14.0 | — |
| pytest | Test execution | Yes | 9.0.2 | — |
| All project deps (click, requests, etc.) | Tests (conftest imports) | Yes | (installed via setup.py) | — |

[VERIFIED: `python3 --version`, `python3 -m pytest --version`, `python3 -m pytest tests/neoload_cli_lib/test_rest_crud.py -q` → 2 passed]

**No missing dependencies.**

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pytest.ini` (in project root) |
| Quick run command | `python3 -m pytest tests/neoload_cli_lib/v4/ -x -q` |
| Full suite command | `python3 -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| D-06 | `v4_endpoint(*segments)` builds correct paths | unit | `python3 -m pytest tests/neoload_cli_lib/v4/test_v4_endpoints.py -x` | No — Wave 0 |
| D-07 | `v4_base()` returns `'v4'` | unit | same | No — Wave 0 |
| D-04 | `v4_workspace_params()` raises CliException when no workspace | unit | same | No — Wave 0 |
| D-04 | `v4_inject_workspace(data)` raises CliException when no workspace | unit | same | No — Wave 0 |
| D-10 | `v4_workspace_params()` returns `{'workspaceId': id}` when workspace set | unit | same | No — Wave 0 |
| D-09/D-08 | `v4_list` returns flat list, paginates correctly | unit | `python3 -m pytest tests/neoload_cli_lib/v4/test_v4_client.py -x` | No — Wave 0 |
| D-09 | `v4_list` unwraps items envelope | unit | same | No — Wave 0 |
| D-12 | `v4_get` delegates to rest_crud.get | unit | same | No — Wave 0 |
| D-11 | `v4_create` injects workspace into body | unit | same | No — Wave 0 |
| D-13 | `v4_update` delegates to rest_crud.patch | unit | same | No — Wave 0 |
| D-14 | `v4_replace` delegates to rest_crud.put | unit | same | No — Wave 0 |
| D-15 | `v4_delete` handles empty 202 body | unit | same | No — Wave 0 |
| D-01 | No existing files modified | verification | `git diff --name-only HEAD` | n/a — post-commit check |

### Sampling Rate

- **Per task commit:** `python3 -m pytest tests/neoload_cli_lib/v4/ -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/neoload_cli_lib/v4/test_v4_endpoints.py` — covers D-04, D-06, D-07, D-10
- [ ] `tests/neoload_cli_lib/v4/test_v4_client.py` — covers D-08, D-09, D-11 through D-15
- [ ] `neoload/neoload_cli_lib/v4/__init__.py` — package marker
- [ ] `neoload/neoload_cli_lib/v4/v4_endpoints.py` — path helpers
- [ ] `neoload/neoload_cli_lib/v4/v4_client.py` — HTTP wrappers

All are new files (Wave 0 = the implementation wave itself).

---

## Security Domain

Not applicable. This phase creates internal library helpers with no user input surfaces, no authentication logic, and no new HTTP endpoints. All security (auth header, SSL, error handling) is inherited from `rest_crud` unchanged.

---

## Sources

### Primary (HIGH confidence)

- `neoload/neoload_cli_lib/rest_crud.py` — exact function signatures verified by direct read
- `neoload/neoload_cli_lib/user_data.py` — `get_meta` return behavior verified lines 209-213
- `neoload/neoload_cli_lib/cli_exception.py` — `CliException` extends `click.ClickException`, verified
- `tests/neoload_cli_lib/test_rest_crud.py` — `monkeypatch.setattr(rest_crud, method, lambda ...)` pattern verified
- `tests/helpers/test_utils.py` — mock helper implementations verified
- `tests/conftest.py` — `neoload_login` fixture, workspace option default is `None`, verified
- `.planning/phases/01-v4-foundation/01-CONTEXT.md` — all locked decisions D-01 through D-17
- `swaggerMerged.yaml` lines 708-733 — `SomePage` schema: `items` + `total` are required; `pageNumber` is 0-indexed, `pageSize` max 200

### Secondary (MEDIUM confidence)

- `find tests -name "__init__.py"` output — absence of `__init__.py` in `tests/neoload_cli_lib/` and `tests/commands/` confirms no init files needed for subdirectories
- `python3 -m pytest tests/neoload_cli_lib/test_rest_crud.py -q` → 2 passed — confirms test suite is runnable

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all imports are project-internal, no new packages
- Architecture: HIGH — verified against actual source files and test structure
- Pitfalls: HIGH — derived from reading actual source code, not assumed
- Inconsistencies with 01-01-PLAN.md: HIGH — line-by-line comparison of plan vs CONTEXT.md decisions

**Research date:** 2026-04-09
**Valid until:** Stable — no external dependencies; only changes if rest_crud.py or user_data.py are modified
