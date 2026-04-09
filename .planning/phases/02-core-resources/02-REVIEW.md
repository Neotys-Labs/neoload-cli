---
phase: 02-core-resources
reviewed: 2026-04-09T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - neoload/commands/v4_results.py
  - neoload/commands/v4_test_executions.py
  - neoload/commands/v4_tests.py
  - neoload/commands/v4_workspaces.py
  - neoload/commands/v4_zones.py
  - tests/commands/test_v4_results.py
  - tests/commands/test_v4_test_executions.py
  - tests/commands/test_v4_tests.py
  - tests/commands/test_v4_workspaces.py
  - tests/commands/test_v4_zones.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-04-09
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

All five command files follow the v4 additive convention correctly (no modifications to existing v2/v3 code, correct file prefixes, shared helpers in `neoload_cli_lib/v4/`). The overall structure is consistent and workspaceId injection is applied correctly — workspace-scoped resources use `v4_create`/`v4_list`, non-scoped resources (workspaces, zones, test-executions) bypass workspace injection as intended.

Three warnings require attention before ship: an unguarded `json.load` in `v4_tests.py` that produces an unhandled exception on invalid input, a potential unhandled `JSONDecodeError` in `v4_test_executions.py` when cancel/force-cancel returns unexpected content, and missing `rest_crud.set_current_command()` instrumentation in `v4_zones.py`. Three info items cover dead-code test guard patterns, a lax test assertion, and missing API error context on `--wait` creation failure.

## Warnings

### WR-01: Unguarded `json.load` in `scenario-update` raises raw exception

**File:** `neoload/commands/v4_tests.py:83`
**Issue:** The `scenario-update` branch calls `json.load(input_file)` without a `try/except` block. Every other `json.load` in the codebase (in `_build_body` for results, tests, test-executions, workspaces, and zones) wraps the call in `try/except json.JSONDecodeError` and raises a clean `CliException`. If a user passes an invalid JSON file to `scenario-update`, a raw `json.JSONDecodeError` propagates to the top level instead of a user-friendly error message.

**Fix:**
```python
# v4_tests.py, scenario-update branch (around line 83)
if not input_file:
    raise cli_exception.CliException('--file is required for scenario-update')
try:
    body = json.load(input_file)
except json.JSONDecodeError as err:
    raise cli_exception.CliException(
        '%s\nThis command requires valid JSON input.' % str(err))
tools.print_json(v4_client.v4_replace('tests', id, 'scenarios', scenario_name, data=body))
```

---

### WR-02: `response.json()` called on non-empty non-JSON body in cancel/force-cancel

**File:** `neoload/commands/v4_test_executions.py:72-74` and `81-83`
**Issue:** Both `cancel` and `force-cancel` call `rest_crud.delete()` directly and then check `if response.content:` before calling `response.json()`. `response.content` is truthy for any non-empty bytes, including whitespace (`b' '`) or a plain-text error body. If the API returns a non-empty, non-JSON 202 body (e.g., a plain-text status string), `response.json()` raises an unhandled `JSONDecodeError`. The `v4_client.v4_delete` helper avoids this by checking `response.status_code == 204 or not response.content`, but the direct calls in this file lack that protection.

**Fix:**
```python
# Apply to both cancel (lines 70-75) and force-cancel (lines 81-86)
response = rest_crud.delete(v4_endpoints.v4_endpoint('test-executions', id))
if response.status_code == 204 or not response.content:
    print('Test execution cancel requested.')
else:
    try:
        tools.print_json(response.json())
    except ValueError:
        print('Test execution cancel requested.')
```

---

### WR-03: Missing `rest_crud.set_current_command()` in `v4_zones.py`

**File:** `neoload/commands/v4_zones.py:25`
**Issue:** The `cli` function in `v4_zones.py` does not call `rest_crud.set_current_command()` or `rest_crud.set_current_sub_command(command)`. All four other command files (`v4_results.py:30-34`, `v4_tests.py:28-32`, `v4_test_executions.py:39-43`, `v4_workspaces.py:29-33`) call both at the top of `cli`. This instrumentation is used for error diagnostics and logging context — its absence means zone errors will lack the current command context in error output.

**Fix:**
```python
def cli(command, zone_id, name, description, zone_type, input_file):
    rest_crud.set_current_command()        # add this
    if not command:
        print("command is mandatory. Please see neoload v4-zones --help")
        return
    rest_crud.set_current_sub_command(command)   # add this
    ...
```

---

## Info

### IN-01: Dead-code test guard pattern `if monkeypatch is None: return`

**File:** `tests/commands/test_v4_results.py:19`, `tests/commands/test_v4_test_executions.py:25`, `tests/commands/test_v4_tests.py:22`, `tests/commands/test_v4_workspaces.py:26`, and ~30 other test methods
**Issue:** Virtually every test method begins with `if monkeypatch is None: return`. The `monkeypatch` fixture in pytest is never `None` — it is always an injected `MonkeyPatch` instance. This guard is unreachable dead code. It obscures test intent and may suppress real failures if a refactor ever changed fixture injection.

**Fix:** Remove all `if monkeypatch is None: return` guards. They are unnecessary.

---

### IN-02: Lax test assertion allows `@` in un-encoded URL

**File:** `tests/commands/test_v4_workspaces.py:202`
**Issue:** The assertion `assert '@' not in captured['endpoint'] or '%40' in captured['endpoint']` uses a disjunction that evaluates to `True` whether or not `@` is actually encoded. If `urllib.parse.urlencode` were replaced with something that left `@` un-encoded, this assertion would still pass (because `'%40' in endpoint` is the second branch, but the `or` means the first branch passing is sufficient to satisfy the whole condition). The test does not actually enforce that `@` is encoded.

**Fix:**
```python
# Replace the lax assertion with an explicit one:
assert 'user%40example.com' in captured['endpoint'] or '%40' in captured['endpoint']
# Or more directly:
assert '@' not in captured['endpoint']
assert '%40' in captured['endpoint']
```

---

### IN-03: API error response hidden when `--wait` creation fails with no execution ID

**File:** `neoload/commands/v4_test_executions.py:53-56`
**Issue:** When `--wait` is set and the `create` call returns a response with no `id` field, a `CliException` is raised immediately but the original API response (`result`) is never printed. If the API returns error detail in the body (e.g., `{'error': 'invalid testId', 'code': 400}`), it is silently discarded before the exception is raised. Other create paths always print the result.

**Fix:**
```python
if wait_completion:
    execution_id = result.get('id')
    if not execution_id:
        tools.print_json(result)  # show API response before raising
        raise cli_exception.CliException('No execution ID returned from create')
    _wait_for_completion(execution_id)
```

---

_Reviewed: 2026-04-09_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
