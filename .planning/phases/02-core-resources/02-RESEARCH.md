# Phase 02: Core Resources - Research

**Researched:** 2026-04-09
**Domain:** NeoLoad CLI v4 command implementation — 5 new command files over the Phase 1 helper layer
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** All 5 command files use the Click argument-based pattern — single `@click.command()` with `click.Choice` for the subcommand argument. Do NOT use `@click.group()`.
- **D-02:** All create/patch commands accept `--file <json_file>` AND named flags. Named flags override file when both provided.
- **D-03:** Key named flags per resource:
  - v4-tests: `--name`, `--description`, `--scenario`
  - v4-results: `--name`, `--description`
  - v4-workspaces: `--name`
  - v4-zones: `--name`, `--description`, `--type` (STATIC/DYNAMIC/CLOUD)
  - v4-test-executions create: `--test-id`, `--scenario`, `--zone-type`, `--duration`
- **D-04:** `create` for test-executions has optional `--wait` flag. Without it: POST and return immediately. With it: poll until terminal status.
- **D-05:** `--wait` exit codes: exit 1 if status is `FAILED` or `TERMINATED`; exit 0 for `PASSED`, `UNKNOWN`, or any other value.
- **D-06:** `logs` subcommand polls `GET /v4/results/{resultId}/logs?offset=N`, printing new lines. Polls until no more new lines. Mirrors existing `neoload logs` command.
- **D-07:** All 5 command files accept resource IDs only for get/patch/delete. No name-based resolution (no Resolver).
- **D-08:** workspaceId is MANDATORY for all workspace-scoped operations. `v4_list` and `v4_create` auto-inject it.
- **D-09:** All commands are additive — zero modifications to any existing file.
- **D-10:** All output uses `tools.print_json()`. No custom formatters or table output.
- **D-11:** All errors raised as `CliException`.

### Claude's Discretion
- Exact polling interval and max-wait timeout for `--wait` and `logs` streaming
- Whether `v4-workspaces ls` injects workspaceId or not (workspace listing is not workspace-scoped)
- Internal structure of the `--wait` polling loop (while loop vs helper function)
- Whether `create` returns the full execution JSON or just the ID when `--wait` is not set

### Deferred Ideas (OUT OF SCOPE)
- v4 name resolver (lookup by name, not just ID)
- Live test monitoring / SLA fastfail during `--wait`
- Log streaming until testExecution reaches terminal status
</user_constraints>

---

## Summary

Phase 2 implements 5 new command files in `neoload/commands/`: `v4_tests.py`, `v4_results.py`, `v4_test_executions.py`, `v4_workspaces.py`, `v4_zones.py`. Each file exports a single `cli` Click command with a `click.Choice` subcommand argument — identical in structure to `test_settings.py`. All commands delegate to the Phase 1 v4_client layer (`v4_list`, `v4_get`, `v4_create`, `v4_update`, `v4_delete`) and `tools.print_json()` for output.

The most complex item is `v4_test_executions.py`, which has two non-trivial behaviors: the `--wait` polling loop polling `GET /v4/test-executions/{id}` until terminal status, and the `logs` subcommand polling `GET /v4/results/{resultId}/logs` with offset pagination until the log stream is exhausted. Both patterns have clear models in the existing codebase (`running_tools.py` polling loop and `logs_tools.py` offset pattern).

The second notable complexity is workspace scoping: `v4-workspaces ls/create/get/patch/delete` and `v4-zones ls/create/get/patch/delete` operate at the system level and do NOT inject workspaceId — they call `v4_get`, `v4_replace`, `v4_delete` directly, not `v4_list`/`v4_create`. Only `v4-tests` and `v4-results` are workspace-scoped (require workspaceId in query params / body). Workspace member operations are workspace-scoped by path (the workspaceId is in the URL, not a query param — handled by calling `v4_get`/`v4_delete` on the full sub-path).

**Primary recommendation:** Follow the `test_settings.py` template precisely for all 5 files. The only novel logic is the `--wait` polling loop and the `logs` offset-polling loop in `v4_test_executions.py`.

---

## Project Constraints (from CLAUDE.md)

- **Branch convention:** This phase executes on `GSD-v4-foundation` (already created); all commits for this phase land there.
- **Additive only:** Zero modifications to existing v2/v3 command or library files.
- **v4_ file prefix:** Command files use `v4_` prefix (`v4_tests.py` → `neoload v4-tests`).
- **Shared v4 helpers:** All v4 HTTP calls go through `neoload/neoload_cli_lib/v4/`.
- **workspaceId mandatory:** For workspace-scoped operations.
- **No new dependencies:** Only packages already in `setup.py install_requires`.

---

## Standard Stack

### Core (Phase 2 — all already present from Phase 1)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | >=7 | CLI framework, `@click.command()` with `click.Choice` | Existing project standard [VERIFIED: setup.py] |
| requests | >=2.25.1 | HTTP client (via rest_crud) | Already in project [VERIFIED: setup.py] |
| json (stdlib) | — | `json.load(file)` for `--file` body input | stdlib, no install [VERIFIED: codebase] |
| time (stdlib) | — | `time.sleep()` for polling loops | stdlib, no install [VERIFIED: codebase] |
| sys (stdlib) | — | `sys.exit()` for `--wait` exit codes | stdlib, no install [VERIFIED: codebase] |

### Phase 1 Helpers (already implemented)
| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `v4_client.py` | All v4 HTTP operations | `v4_list`, `v4_get`, `v4_create`, `v4_update`, `v4_replace`, `v4_delete` |
| `v4_endpoints.py` | Path and workspace utilities | `v4_endpoint()`, `v4_workspace_params()`, `v4_inject_workspace()` |

### Infrastructure (already present)
| Module | Purpose |
|--------|---------|
| `rest_crud.py` | `set_current_command()`, `set_current_sub_command()` |
| `tools.py` | `print_json()`, `is_id()` |
| `cli_exception.py` | `CliException` |
| `user_data.py` | `get_meta()` |

**No installation needed** — all dependencies already in setup.py.

---

## Architecture Patterns

### Recommended Project Structure
```
neoload/commands/
├── v4_tests.py            # neoload v4-tests
├── v4_results.py          # neoload v4-results
├── v4_test_executions.py  # neoload v4-test-executions
├── v4_workspaces.py       # neoload v4-workspaces
└── v4_zones.py            # neoload v4-zones

tests/commands/
├── test_v4_tests.py
├── test_v4_results.py
├── test_v4_test_executions.py
├── test_v4_workspaces.py
└── test_v4_zones.py
```

### Pattern 1: Standard Click Choice Command (all 5 files)
**What:** A single `@click.command()` function with `click.Choice` subcommand argument, named flags, and a dispatch block.
**When to use:** All 5 command files — identical outer structure.

```python
# Source: neoload/commands/test_settings.py (canonical example)
import json
import sys
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_client, v4_endpoints

@click.command()
@click.argument('command', type=click.Choice([
    'ls', 'create', 'get', 'patch', 'delete'
], case_sensitive=False), required=False)
@click.argument('id', type=str, required=False)
@click.option('--name', help="Resource name")
@click.option('--file', type=click.File('r'), help="JSON body file")
def cli(command, id, name, file):
    """..."""
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-<resource> --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'ls':
        tools.print_json(v4_client.v4_list('resource-path'))
        return
    if command == 'create':
        body = _build_body(file, name=name)
        tools.print_json(v4_client.v4_create('resource-path', data=body))
        return
    # ... get/patch/delete dispatch on id
```

### Pattern 2: Body Building (create/patch)
**What:** Load from `--file` if provided, then overlay named flags (non-None values only).
**When to use:** All create and patch subcommands (D-02, D-03).

```python
# Source: derived from test_settings.py create_json() pattern
def _build_body(file, name=None, description=None):
    body = {}
    if file:
        try:
            body = json.load(file)
        except json.JSONDecodeError as err:
            raise cli_exception.CliException(
                '%s\nThis command requires valid JSON input.' % str(err))
    # Named flags override file values (non-None only)
    if name is not None:
        body['name'] = name
    if description is not None:
        body['description'] = description
    return body
```

### Pattern 3: --wait Polling Loop (v4_test_executions create)
**What:** POST to create test execution, then poll `GET /v4/test-executions/{id}` until terminal status. Exit 1 on FAILED/TERMINATED, exit 0 otherwise.
**When to use:** `v4-test-executions create --wait` only.

```python
# Source: running_tools.py pattern adapted for v4 test execution
import time, sys

TERMINAL_STATUSES = {'FAILED', 'TERMINATED', 'CANCELLED', 'STARTED_TEST',
                     'FAILED_TO_PREPARE_CONTROLLER', 'FAILED_TO_PREPARE_LGS'}
FAIL_EXIT_STATUSES = {'FAILED', 'TERMINATED'}
POLL_INTERVAL_SECONDS = 5

def _wait_for_completion(execution_id):
    while True:
        result = v4_client.v4_get('test-executions', execution_id)
        step = result.get('step', '')
        if step in TERMINAL_STATUSES:
            tools.print_json(result)
            if step in FAIL_EXIT_STATUSES:
                sys.exit(1)
            return
        time.sleep(POLL_INTERVAL_SECONDS)
```

**Note on terminal statuses from API spec:** `GET /v4/test-executions/{id}` returns a `step` field (not `status`) with values: `INITIALIZING`, `PREPARING_CONTROLLER`, `FAILED_TO_PREPARE_CONTROLLER`, `PREPARING_LGS`, `FAILED_TO_PREPARE_LGS`, `SENDING_PROJECT`, `FAILED`, `PREPARING_TEST`, `STARTING_TEST`, `STARTED_TEST`, `CANCELLED`. The decisions map `FAILED` and `TERMINATED` to exit 1. `TERMINATED` does not appear in the `step` enum — it appears in result `status` on `v4/results`. Clarification needed (see Open Questions #1). [VERIFIED: nlweb-bench-runtime-rest.yaml `GetTestExecutionResponse.step`]

### Pattern 4: Logs Offset Polling (v4_test_executions logs)
**What:** Poll `GET /v4/results/{resultId}/logs?pageNumber=N` collecting all log entries until no new items are returned.
**When to use:** `v4-test-executions logs <resultId>`.

```python
# Source: logs_tools.py pattern adapted with v4 endpoint + pagination
import time

POLL_INTERVAL_SECONDS = 2

def _poll_logs(result_id):
    page_number = 0
    while True:
        response = v4_client.v4_get('results', result_id, 'logs',
                                     params={'pageNumber': page_number})
        # Note: v4_get does not accept params; use rest_crud.get directly
        # with v4_endpoints.v4_endpoint for this call
        items = response.get('items', [])
        for entry in items:
            print(entry.get('date', ''), entry.get('level', ''), entry.get('line', ''))
        total = response.get('total', 0)
        fetched_so_far = (page_number + 1) * len(items)
        if fetched_so_far >= total or not items:
            break
        page_number += 1
        time.sleep(POLL_INTERVAL_SECONDS)
```

**Important:** `v4_get` has no `params` argument. For the logs endpoint which requires `pageNumber`/`pageSize` query params, either: (a) use `rest_crud.get(v4_endpoints.v4_endpoint(...), params)` directly, or (b) use `v4_list` without workspace injection by calling `rest_crud.get` directly. The simplest approach is to call `rest_crud.get` with `v4_endpoints.v4_endpoint('results', result_id, 'logs')` and the params dict directly. [VERIFIED: v4_client.py — `v4_get` signature has no params]

### Pattern 5: Non-Workspace-Scoped Resources (workspaces, zones)
**What:** `v4-workspaces` and `v4-zones` operate at the system level — no workspaceId injection.
**When to use:** All subcommands in `v4_workspaces.py` and `v4_zones.py`.

```python
# Source: v4_client.py — v4_get, v4_replace, v4_delete do not inject workspaceId

# ls for workspaces — does NOT use v4_list (which injects workspaceId)
# Use rest_crud.get directly with pagination params
def _workspace_list():
    page_number = 0
    page_size = 200
    all_items = []
    while True:
        response = rest_crud.get(
            v4_endpoints.v4_endpoint('workspaces'),
            {'pageNumber': page_number, 'pageSize': page_size}
        )
        items = response.get('items', [])
        all_items.extend(items)
        if len(all_items) >= response.get('total', 0) or not items:
            break
        page_number += 1
    return all_items
```

### Pattern 6: Workspace Member Operations
**What:** `members-ls`, `members-add`, `members-remove` call sub-paths on `workspaces/{id}/members`.
**When to use:** Three additional subcommands in `v4_workspaces.py`.

```python
# Source: API spec ntweb-security-sso-rest.yaml
# GET  /v4/workspaces/{workspaceId}/members  → v4_get('workspaces', ws_id, 'members')
# POST /v4/workspaces/{workspaceId}/members  → v4_create('workspaces', ws_id, 'members', data=body)
#   BUT: members-add body has {userId, role} — no workspaceId injection needed in body
#        so v4_create is wrong here (it injects workspaceId)
#   Use rest_crud.post directly for members-add
# DELETE /v4/workspaces/{workspaceId}/members?login=X  → rest_crud.delete(endpoint + '?login=' + login)
#   OR pass params; rest_crud.delete has no params arg — use requests directly or encode in URL
```

**Note:** `members-add` body schema is `WorkspaceMemberPostRequest` — does NOT have workspaceId in body; `v4_create` would incorrectly inject workspaceId into the body. Use `rest_crud.post` directly. Similarly `members-remove` uses DELETE with a `?login=` query param — `rest_crud.delete` has no params argument. The planner must choose: encode login in the URL path, or use `rest_crud.get_raw`/direct HTTP. See Open Questions #2. [VERIFIED: ntweb-security-sso-rest.yaml, v4_client.py]

### Pattern 7: v4-workspaces subscription
**What:** `GET /v4/workspaces/{workspaceId}/subscription` — read-only workspace subscription info.
**Where:** `neoload/nlweb-apis-gateway/rest/src/main/resources/nlweb-apis-gateway-rest.yaml` line 1133.

```python
# v4_get('workspaces', ws_id, 'subscription')
```

### Anti-Patterns to Avoid
- **Using `click.group()` with subcommands:** The project uses `click.Choice` argument. Never `@resource_group.command()`.
- **Calling rest_crud directly for workspace-scoped ops:** Always go through v4_client for tests/results creates (ensures workspaceId injection).
- **Using `v4_list` for zones/workspaces:** `v4_list` injects workspaceId; zones and workspaces are not workspace-scoped.
- **Using `v4_create` for workspace members-add:** `v4_create` injects workspaceId into the POST body; members body schema does not include workspaceId.
- **Forgetting to call `rest_crud.set_current_command()` and `set_current_sub_command()`:** Every command function must call these two at the start — required for the User-Agent header telemetry in `rest_crud.add_user_agent()`.
- **Not guarding against missing command:** Always `if not command: print(...); return` before dispatch.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pagination over v4 pages | Custom page loop for tests/results | `v4_client.v4_list` | Already handles pageNumber/pageSize iteration, workspaceId injection |
| JSON output formatting | Custom dict-to-string | `tools.print_json()` | Consistent indent=2, ensure_ascii=False across all commands |
| Error handling | try/except around HTTP calls | `rest_crud.__handle_error` + `CliException` | rest_crud already raises CliException on non-2xx; just raise CliException for business logic errors |
| File JSON parsing | Custom open/read | `click.File('r')` + `json.load()` | Click handles file not found, permission errors; json.load handles decode errors |
| Zone list pagination | Manual while loop | Direct `rest_crud.get` with page params | Same pattern as _workspace_list — but note zones API has no workspaceId filter |
| Auto-discovery | Registering commands in `__main__.py` | Filename convention (`v4_*.py` in commands/) | NeoLoadCLI auto-discovers any `.py` file in commands/ that doesn't start with `__init__` |

**Key insight:** The Phase 1 layer already handles the hardest parts (workspace injection, pagination, error propagation). Phase 2 command files are thin wrappers that translate CLI flags into v4_client calls.

---

## API Endpoint Reference (Verified from Specs)

### v4-tests
| Subcommand | HTTP | Path | Workspace-scoped | Spec Source |
|-----------|------|------|-----------------|-------------|
| ls | GET | /v4/tests?workspaceId=X | Yes (query param) | nlweb-bench-definition-rest.yaml:1331 |
| create | POST | /v4/tests | Yes (body field) | nlweb-bench-definition-rest.yaml:1456 |
| get | GET | /v4/tests/{testId} | No | nlweb-bench-definition-rest.yaml:1523 |
| patch | PATCH | /v4/tests/{testId} | No | nlweb-bench-definition-rest.yaml:1673 |
| delete | DELETE | /v4/tests/{testId} | No | nlweb-bench-definition-rest.yaml:1595 |
| scenario-get | GET | /v4/tests/{testId}/scenarios/{scenarioName} | No | nlweb-bench-definition-rest.yaml:1824 |
| scenario-update | PUT | /v4/tests/{testId}/scenarios/{scenarioName} | No | nlweb-bench-definition-rest.yaml:1910 |

**test-delete note:** API spec accepts optional `?deleteResults=true` query param. CLI should expose this as `--delete-results` flag (Claude's discretion). [VERIFIED: nlweb-bench-definition-rest.yaml:1619]

**scenario-get/update note:** Only scenarioName `custom` is currently valid per API spec. The second argument should be either hardcoded to `custom` or accept any string and let the API return the error. [VERIFIED: nlweb-bench-definition-rest.yaml:1844]

### v4-results
| Subcommand | HTTP | Path | Workspace-scoped | Spec Source |
|-----------|------|------|-----------------|-------------|
| ls | GET | /v4/results?workspaceId=X | Yes (query param) | nlweb-bench-definition-rest.yaml:777 |
| get | GET | /v4/results/{resultId} | No | nlweb-bench-definition-rest.yaml:1042 |
| patch | PATCH | /v4/results/{resultId} | No | (inferred from pattern) |
| delete | DELETE | /v4/results/{resultId} | No | (inferred from pattern) |
| contexts | GET | /v4/results/{resultId}/contexts | No | nlweb-bench-definition-rest.yaml:1262 |
| elements | GET | /v4/results/{resultId}/elements | No | nlweb-bench-definition-rest.yaml:434 |
| monitors | GET | /v4/results/{resultId}/monitors | No | nlweb-bench-definition-rest.yaml:501 |
| statistics | GET | /v4/results/{resultId}/statistics | No | nlweb-bench-definition-rest.yaml:573 |
| timeseries | GET | /v4/results/{resultId}/timeseries | No | nlweb-bench-definition-rest.yaml:651 |
| search-criteria | GET | /v4/results/search-criteria?workspaceId=X | Yes (query param) | nlweb-bench-definition-rest.yaml:976 |

**search-criteria note:** This is a GET on `/v4/results/search-criteria` — not a sub-resource by ID. It requires workspaceId as query param. Call `rest_crud.get(v4_endpoints.v4_endpoint('results', 'search-criteria'), v4_endpoints.v4_workspace_params())`. [VERIFIED: nlweb-bench-definition-rest.yaml:976]

### v4-test-executions
| Subcommand | HTTP | Path | Notes |
|-----------|------|------|-------|
| create | POST | /v4/test-executions | Does NOT inject workspaceId; testId in body |
| get | GET | /v4/test-executions/{testExecutionId} | — |
| cancel | DELETE | /v4/test-executions/{testExecutionId} | Returns 202 (no body) |
| force-cancel | DELETE | /v4/test-executions/{testExecutionId}/forced | Returns 202 (no body) |
| logs | GET | /v4/results/{resultId}/logs | Paginated; resultId == testExecutionId |

**Spec source:** nlweb-bench-runtime-rest.yaml

**create body:** `TestExecutionInput` — only `testId` is required. Optional: `description`, `duration`, `name`, `reservationId`, `sapVu`, `webVu`. The `--test-id`, `--scenario`, `--zone-type`, `--duration` flags from D-03 map to: `testId`, _(no scenario field in TestExecutionInput)_, _(no zoneType field in TestExecutionInput)_, `duration`. Note: `scenario` and `zone-type` are NOT fields in `TestExecutionInput` per the spec — the scenario and zone come from the test settings referenced by `testId`. These flags may be ASSUMED or map to fields not in the spec. See Open Questions #3. [VERIFIED: nlweb-bench-runtime-rest.yaml `TestExecutionInput`]

**logs endpoint:** Returns `ResultLogsResponse` with `items[]` (each has `date`, `level`, `line`), `total`, `pageNumber`, `pageSize`. The `date` field is ISO8601 string. No `offset` parameter — uses `pageNumber`/`pageSize` pagination. [VERIFIED: nlweb-bench-runtime-rest.yaml `ResultLogsResponse`]

**v4_delete returns None on 202:** v4_client.v4_delete checks `status_code == 204 or not response.content`. Cancel returns 202 with empty body — `not response.content` is True, so returns None. `tools.print_json(None)` would fail — command must handle None result from cancel/force-cancel. [VERIFIED: v4_client.py:87-88]

### v4-workspaces
| Subcommand | HTTP | Path | Spec Source |
|-----------|------|------|-------------|
| ls | GET | /v4/workspaces | ntweb-security-sso-rest.yaml:2606 |
| create | POST | /v4/workspaces | ntweb-security-sso-rest.yaml:2683 |
| get | GET | /v4/workspaces/{workspaceId} | ntweb-security-sso-rest.yaml:2738 |
| patch | PATCH | /v4/workspaces/{workspaceId} | ntweb-security-sso-rest.yaml:2807 |
| delete | DELETE | /v4/workspaces/{workspaceId} | nlweb-apis-gateway-rest.yaml:1613 |
| members-ls | GET | /v4/workspaces/{workspaceId}/members | ntweb-security-sso-rest.yaml:2880 |
| members-add | POST | /v4/workspaces/{workspaceId}/members | ntweb-security-sso-rest.yaml:2949 |
| members-remove | DELETE | /v4/workspaces/{workspaceId}/members?login=X | ntweb-security-sso-rest.yaml:3029 |
| subscription | GET | /v4/workspaces/{workspaceId}/subscription | nlweb-apis-gateway-rest.yaml:1133 |

**Workspace ID format:** MongoDB ObjectId (`^[0-9a-f]{24}$`) — NOT UUID. `tools.is_id()` checks UUID format; `tools.is_mongodb_id()` checks the MongoDB format. Use `tools.is_mongodb_id()` for workspace IDs. [VERIFIED: ntweb-security-sso-rest.yaml `workspaceId` schema pattern]

**members-add body:** `WorkspaceMemberPostRequest` — does NOT include workspaceId. Cannot use `v4_create` (which injects workspaceId into body). Use `rest_crud.post(v4_endpoints.v4_endpoint('workspaces', ws_id, 'members'), body)` directly. [VERIFIED: ntweb-security-sso-rest.yaml:2972]

**members-remove:** `DELETE /v4/workspaces/{workspaceId}/members?login=X` — `rest_crud.delete` does not accept query params. Encode login in URL: `rest_crud.delete(v4_endpoints.v4_endpoint('workspaces', ws_id, 'members') + '?login=' + login)`. [VERIFIED: ntweb-security-sso-rest.yaml:3038-3044, rest_crud.py:160]

### v4-zones
| Subcommand | HTTP | Path | Notes | Spec Source |
|-----------|------|------|-------|-------------|
| ls | GET | /v4/zones | No workspaceId. Optional `?type=STATIC|DYNAMIC|CLOUD` | nlweb-apis-gateway-rest.yaml:1680 |
| create | POST | /v4/zones | Body: `PostZoneFields` | nlweb-apis-gateway-rest.yaml:1775 |
| get | GET | /v4/zones/{zoneId} | — | nlweb-apis-gateway-rest.yaml:1902 |
| patch | PATCH or PUT | /v4/zones/{zoneId} | Spec shows PUT (full replace), not PATCH | nlweb-apis-gateway-rest.yaml:1976 |
| delete | DELETE | /v4/zones/{zoneId} | Returns 202 | nlweb-apis-gateway-rest.yaml:2047 |

**Zone ID format:** NOT UUID — alphanumeric 5-6 chars pattern `^([0-9a-zA-Z]{5,6}|defaultzone)$`. Do not validate with `tools.is_id()`. [VERIFIED: nlweb-apis-gateway-rest.yaml:1916-1918]

**Zone patch vs put:** The API spec shows `PUT /v4/zones/{zoneId}` for updating a zone (operationId: `ZonesResource.put`), and `PATCH /v4/zones` (collection level) for patchAll with dryRun. The CONTEXT.md calls it "patch" subcommand. Implementation should use `v4_replace` (PUT) for the `patch` subcommand, or verify if a PATCH on single zone exists. See Open Questions #4. [VERIFIED: nlweb-apis-gateway-rest.yaml:1829, 1976]

---

## Common Pitfalls

### Pitfall 1: v4_list Workspace Injection for Non-Scoped Resources
**What goes wrong:** Using `v4_client.v4_list('workspaces')` or `v4_client.v4_list('zones')` raises `CliException("No workspace set")` even if the user has no workspace configured — because `v4_list` always calls `v4_workspace_params()`.
**Why it happens:** `v4_list` unconditionally injects workspaceId as a query param. Zones and workspaces list endpoints do NOT accept workspaceId.
**How to avoid:** For zones and workspaces `ls`, call `rest_crud.get(v4_endpoints.v4_endpoint('zones'), params)` directly.
**Warning signs:** Test fails with "No workspace set" on zones/workspaces commands even when workspace is irrelevant.

### Pitfall 2: tools.print_json(None) Crash
**What goes wrong:** `cancel` and `force-cancel` return 202 with empty body. `v4_client.v4_delete` returns `None` for these. `tools.print_json(None)` calls `json.dumps(None)` which outputs `"null"` — this is actually OK (prints `null`). However, if code does `tools.get_id_and_print_json(None)` it will crash with a KeyError.
**Why it happens:** Pattern from older commands uses `get_id_and_print_json`; v4 commands should use `print_json`.
**How to avoid:** Use `tools.print_json(result)` where result may be None. Or check `if result: tools.print_json(result)` and print a success message otherwise.
**Warning signs:** AttributeError or TypeError on cancel command.

### Pitfall 3: Step vs Status Confusion in --wait
**What goes wrong:** `GET /v4/test-executions/{id}` returns a `step` field (workflow step, not the result status). The CONTEXT.md decisions mention `FAILED` and `TERMINATED` as terminal statuses. `TERMINATED` appears as a result status (on the result object) but NOT as a valid `step` value in the test-execution response. Polling may run forever if checking for `TERMINATED` in `step`.
**Why it happens:** The test execution step enum is different from the result status enum.
**How to avoid:** Poll `step` field; treat `FAILED`, `CANCELLED`, `FAILED_TO_PREPARE_CONTROLLER`, `FAILED_TO_PREPARE_LGS`, `STARTED_TEST` as terminal steps. The result's final quality status (PASSED/FAILED/UNKNOWN) is on the result object, not the execution step.
**Warning signs:** `--wait` loop never exits.

### Pitfall 4: Workspace ID Format Detection
**What goes wrong:** Using `tools.is_id()` to validate a workspace ID always returns False because workspace IDs use MongoDB ObjectId format (24 hex chars), not UUID format (8-4-4-4-12).
**Why it happens:** The existing v2/v3 `workspaces.py` uses `tools.is_mongodb_id()`. v4_workspaces.py must also use `is_mongodb_id()`.
**How to avoid:** Use `tools.is_mongodb_id(workspace_id)` for workspace ID validation.
**Warning signs:** Workspace get/patch/delete silently accepts any string without validation.

### Pitfall 5: rest_crud.delete Has No params Argument
**What goes wrong:** `rest_crud.delete(endpoint)` signature has no `params` parameter. Attempting `rest_crud.delete(endpoint, params={'login': 'user'})` raises TypeError.
**Why it happens:** The `delete` function in rest_crud only takes `endpoint: str`.
**How to avoid:** For members-remove, append the query string to the URL: `rest_crud.delete(endpoint + '?login=' + login)`.
**Warning signs:** TypeError "delete() got an unexpected keyword argument 'params'".

### Pitfall 6: v4_create Injects workspaceId for Non-Workspace Body Operations
**What goes wrong:** Using `v4_create('workspaces', ws_id, 'members', data=body)` injects `workspaceId` into the POST body. The members-add body schema (`WorkspaceMemberPostRequest`) does not expect workspaceId.
**Why it happens:** `v4_create` always calls `v4_inject_workspace(data)` before posting.
**How to avoid:** For any POST where the body does NOT include workspaceId, call `rest_crud.post(v4_endpoints.v4_endpoint(...), body)` directly.
**Warning signs:** 400 Bad Request from API due to unexpected field.

### Pitfall 7: Auto-Discovery Filename Convention
**What goes wrong:** If a command file is named differently (e.g., `commands/v4tests.py` instead of `commands/v4_tests.py`), the CLI command name will not match the expected `neoload v4-tests`.
**Why it happens:** `__main__.py` replaces `_` with `-` in filenames. `v4_tests.py` → `v4-tests`. `v4tests.py` → `v4tests`.
**How to avoid:** Always use underscore word separator in filename: `v4_tests.py`, `v4_results.py`, `v4_test_executions.py`, `v4_workspaces.py`, `v4_zones.py`.
**Warning signs:** `neoload v4-tests` → "is not a neoload command".

---

## Code Examples

### Complete Minimal v4 Command File (v4_zones.py sketch)
```python
# Source: test_settings.py + workspaces.py patterns + v4_client API
import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_client, v4_endpoints


@click.command()
@click.argument('command', type=click.Choice(
    ['ls', 'create', 'get', 'patch', 'delete'], case_sensitive=False
), required=False)
@click.argument('zone_id', type=str, required=False)
@click.option('--name', help='Zone name')
@click.option('--description', help='Zone description')
@click.option('--type', 'zone_type', type=click.Choice(['STATIC', 'DYNAMIC', 'CLOUD']),
              help='Zone type')
@click.option('--file', type=click.File('r'), help='JSON body file')
def cli(command, zone_id, name, description, zone_type, file):
    """v4 zone management: ls, create, get, patch, delete"""
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-zones --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'ls':
        # Zones are NOT workspace-scoped — cannot use v4_list
        response = rest_crud.get(v4_endpoints.v4_endpoint('zones'))
        tools.print_json(response.get('items', response))
        return

    if command == 'create':
        body = _build_body(file, name=name, description=description, zone_type=zone_type)
        tools.print_json(rest_crud.post(v4_endpoints.v4_endpoint('zones'), body))
        return

    if not zone_id:
        raise cli_exception.CliException('zone_id is required for ' + command)

    if command == 'get':
        tools.print_json(v4_client.v4_get('zones', zone_id))
    elif command == 'patch':
        body = _build_body(file, name=name, description=description, zone_type=zone_type)
        tools.print_json(v4_client.v4_replace('zones', zone_id, data=body))
    elif command == 'delete':
        v4_client.v4_delete('zones', zone_id)
        print('Zone deleted.')


def _build_body(file, name=None, description=None, zone_type=None):
    body = {}
    if file:
        try:
            body = json.load(file)
        except json.JSONDecodeError as err:
            raise cli_exception.CliException(
                '%s\nThis command requires valid JSON.' % str(err))
    if name is not None:
        body['name'] = name
    if description is not None:
        body['description'] = description
    if zone_type is not None:
        body['type'] = zone_type
    return body
```

### Test Pattern for v4 Command (monkeypatch approach)
```python
# Source: tests/neoload_cli_lib/v4/test_v4_client.py pattern
import pytest
from click.testing import CliRunner
from neoload_cli_lib import rest_crud, user_data
from commands.v4_zones import cli

MOCK_WORKSPACE_ID = '5e3acde2e860a132744ca916'

@pytest.mark.usefixtures("neoload_login")
class TestV4ZonesLs:
    def test_ls_returns_zones(self, monkeypatch):
        if monkeypatch is None:
            return
        monkeypatch.setattr(rest_crud, 'get',
            lambda endpoint, params=None: {'items': [{'id': 'aBcDe', 'name': 'z1'}], 'total': 1})
        runner = CliRunner()
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert 'aBcDe' in result.output
```

---

## Runtime State Inventory

Step 2.5: SKIPPED — Phase 2 is a greenfield feature addition (no rename/refactor/migration involved).

---

## Environment Availability

Step 2.6: External dependencies for Phase 2 are limited to the existing test framework.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | All code | Yes | 3.x (3.14 per cache paths) | — |
| pytest | Test suite | Yes | 9.0.2 (per pycache paths) | — |
| Click | CLI framework | Yes | >=7 in setup.py | — |
| pytest-datafiles | Tests | Yes | in setup.py tests_require | — |

[VERIFIED: pycache directory names show cpython-314-pytest-9.0.2, setup.py]

**No missing dependencies.** All required tools are present.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None detected (uses defaults) |
| Quick run command | `pytest tests/commands/test_v4_tests.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map

| Behavior | Test Type | Automated Command | Notes |
|----------|-----------|-------------------|-------|
| v4-tests ls returns paginated list | unit | `pytest tests/commands/test_v4_tests.py -x -k ls` | Wave 0: create file |
| v4-tests create POSTs with workspaceId | unit | `pytest tests/commands/test_v4_tests.py -x -k create` | Wave 0 |
| v4-tests get/patch/delete by ID | unit | `pytest tests/commands/test_v4_tests.py -x -k "get or patch or delete"` | Wave 0 |
| v4-tests scenario-get/scenario-update | unit | `pytest tests/commands/test_v4_tests.py -x -k scenario` | Wave 0 |
| v4-results ls/get/patch/delete | unit | `pytest tests/commands/test_v4_results.py -x` | Wave 0 |
| v4-results sub-resources (contexts, elements, etc.) | unit | `pytest tests/commands/test_v4_results.py -x -k "contexts or elements"` | Wave 0 |
| v4-test-executions create (no --wait) | unit | `pytest tests/commands/test_v4_test_executions.py -x -k "create"` | Wave 0 |
| v4-test-executions create --wait polls and exits 1 on FAILED | unit | `pytest tests/commands/test_v4_test_executions.py -x -k "wait"` | Wave 0 |
| v4-test-executions logs polls until empty | unit | `pytest tests/commands/test_v4_test_executions.py -x -k "logs"` | Wave 0 |
| v4-workspaces ls (no workspaceId) | unit | `pytest tests/commands/test_v4_workspaces.py -x -k "ls"` | Wave 0 |
| v4-workspaces members-add/remove | unit | `pytest tests/commands/test_v4_workspaces.py -x -k "members"` | Wave 0 |
| v4-zones ls/create/get/patch/delete | unit | `pytest tests/commands/test_v4_zones.py -x` | Wave 0 |
| Error: missing command arg | unit | included in each file's tests | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/commands/test_v4_<file>.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
All 5 test files need to be created:
- [ ] `tests/commands/test_v4_tests.py`
- [ ] `tests/commands/test_v4_results.py`
- [ ] `tests/commands/test_v4_test_executions.py`
- [ ] `tests/commands/test_v4_workspaces.py`
- [ ] `tests/commands/test_v4_zones.py`

Also verify `tests/commands/` directory exists:
- [ ] `tests/commands/__init__.py` — may need to be created if directory is new

---

## Security Domain

Security enforcement not configured as disabled. Applying minimal ASVS review for CLI tool context.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Auth handled upstream by existing `login` command and `accountToken` header |
| V3 Session Management | No | Stateless CLI; tokens stored by existing user_data module |
| V4 Access Control | No | API-side enforcement; CLI passes credentials, does not enforce roles |
| V5 Input Validation | Minimal | `click.Choice` enforces subcommand values; `json.load` validates JSON files |
| V6 Cryptography | No | No crypto in Phase 2 |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| JSON injection via --file | Tampering | `json.load` parses and validates; malformed JSON raises CliException |
| ID injection in URL path | Tampering | IDs come from API responses; no free-form path concatenation beyond what `v4_endpoint` does |
| Token leakage via --debug logs | Information Disclosure | Existing `rest_crud` logs body (not headers); accountToken is in headers only |

**Assessment:** Phase 2 has minimal security surface. It passes user-provided IDs into URL paths via `v4_endpoints.v4_endpoint()` (string join, no SQL or shell injection risk). The main risk is passing malformed JSON via `--file`; this is handled by `json.load` raising `json.JSONDecodeError`.

---

## Open Questions (RESOLVED)

1. **terminal statuses for `--wait` polling: `step` vs expected values from D-05**
   - **RESOLVED:** User confirmed CANCELLED is the v4 equivalent of TERMINATED (D-05 updated in CONTEXT.md). `FAIL_EXIT_STEPS = {'FAILED', 'CANCELLED'}`. Exit 0 on PASSED or any other value.

2. **members-remove via URL-encoded query param**
   - **RESOLVED:** Use `urllib.parse.urlencode({'login': login})` for safe encoding. Implemented in Plan 04 as `rest_crud.delete(endpoint + '?' + urlencode({'login': login}))`.

3. **--scenario and --zone-type flags on test-executions create**
   - **RESOLVED:** User confirmed these are pass-through flags (D-03 updated in CONTEXT.md). `--scenario` writes to body as `scenarioName`; `--zone-type` writes as `zoneType`. API server validates; CLI does not reject unknown fields. Implemented in Plan 03.

4. **Zone patch subcommand uses PUT, not PATCH**
   - **RESOLVED:** Plan 05 uses `v4_client.v4_replace` (PUT) internally for the `patch` subcommand. Help text documents that this is a full replace (PUT) despite the subcommand name.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `v4_workspaces ls` does not require workspaceId in query params | Architecture Patterns / API Endpoint Reference | If wrong, ls would return 400; user would see confusing error |
| A2 | `v4_zones ls` does not require workspaceId in query params | API Endpoint Reference | Same as A1 |
| A3 | `tests/commands/` directory does not yet exist | Validation Architecture | If wrong, test file placement needs adjustment (but new files are harmless either way) |
| A4 | `CANCELLED` step is the appropriate exit-1 equivalent for `TERMINATED` in D-05 | Common Pitfalls / Open Questions | If wrong, `--wait` may not signal test cancellation correctly |

---

## Sources

### Primary (HIGH confidence)
- `neoload/neoload_cli_lib/v4/v4_endpoints.py` — verified function signatures
- `neoload/neoload_cli_lib/v4/v4_client.py` — verified function signatures and workspace injection behavior
- `neoload/commands/test_settings.py` — canonical Click Choice pattern
- `neoload/commands/logs.py`, `neoload/neoload_cli_lib/logs_tools.py` — log polling pattern
- `neoload/neoload_cli_lib/running_tools.py` — --wait polling pattern
- `neoload/neoload_cli_lib/rest_crud.py` — delete signature (no params), set_current_command
- `neoload/__main__.py` — auto-discovery filename convention confirmed
- `/neoload/nlweb-bench-runtime/rest/src/main/resources/nlweb-bench-runtime-rest.yaml` — test-executions and logs endpoints
- `/neoload/nlweb-bench-definition/rest/src/main/resources/nlweb-bench-definition-rest.yaml` — tests and results endpoints
- `/neoload/nlweb-apis-gateway/rest/src/main/resources/nlweb-apis-gateway-rest.yaml` — zones, workspaces delete, analytics
- `/neoload/ntweb-security-sso/rest/src/main/resources/ntweb-security-sso-rest.yaml` — workspaces CRUD + members
- `setup.py` — verified available dependencies

### Secondary (MEDIUM confidence)
- `tests/neoload_cli_lib/v4/test_v4_client.py` — test class structure pattern to follow
- `tests/conftest.py` — `neoload_login` fixture, monkeypatch guard pattern

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies verified from setup.py and existing code
- Architecture patterns: HIGH — all patterns verified from existing command files
- API endpoint details: HIGH — verified from OpenAPI YAML specs
- Pitfalls: HIGH — verified from direct code inspection (v4_client.py signatures, rest_crud.py delete, tools.py is_id vs is_mongodb_id)
- Open questions: MEDIUM — items require planner/user decision, not additional research

**Research date:** 2026-04-09
**Valid until:** 2026-07-09 (stable — API spec and codebase unlikely to change)
