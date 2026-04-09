# Phase 02: Core Resources - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement 5 new v4 command files: `v4_tests.py`, `v4_results.py`, `v4_test_executions.py`, `v4_workspaces.py`, `v4_zones.py`. Each becomes a CLI command group discoverable via the existing filename-convention auto-discovery. No existing files are modified.

</domain>

<decisions>
## Implementation Decisions

### CLI Structure
- **D-01:** All 5 command files use the Click argument-based pattern — single `@click.command()` with `click.Choice` for the subcommand argument. Consistent with every existing v2/v3 command. Do NOT use `@click.group()` with per-subcommand decorators.

### Body Input (create/patch operations)
- **D-02:** All create/patch commands accept `--file <json_file>` for a full JSON body AND a small set of named flags for the most commonly-used fields. Named flags override values from the file when both are provided.
- **D-03:** Key named flags per resource:
  - v4-tests: `--name`, `--description`, `--scenario`
  - v4-results: `--name`, `--description`
  - v4-workspaces: `--name`
  - v4-zones: `--name`, `--description`, `--type` (STATIC/DYNAMIC/CLOUD)
  - v4-test-executions create: `--test-id`, `--scenario`, `--zone-type`, `--duration` (full config still via `--file`)

### v4-test-executions: create
- **D-04:** `create` subcommand has an optional `--wait` flag. Without `--wait`, it POSTs and immediately returns the testExecutionId JSON. With `--wait`, it polls `GET /v4/test-executions/{id}` until a terminal status is reached.
- **D-05:** Terminal statuses for `--wait` exit code logic: exit 1 if status is `FAILED` or `TERMINATED`; exit 0 if status is `PASSED`, `UNKNOWN`, or any other value.

### v4-test-executions: logs
- **D-06:** `logs` subcommand polls `GET /v4/results/{resultId}/logs?offset=N`, printing new log lines as they arrive. Continues polling until no more new lines are returned. Mirrors the behavior of the existing `neoload logs` command.

### Name/ID Resolution
- **D-07:** All 5 command files accept resource IDs only for operations like `get`, `patch`, `delete`. No name-based resolution (no Resolver). Users obtain IDs from `ls` output. This keeps commands simple and avoids an additional list-and-filter round-trip per operation.

### Inherited from Phase 1 (unchanged)
- **D-08:** workspaceId is MANDATORY for all workspace-scoped operations. `v4_list` and `v4_create` auto-inject it. Commands for workspace-free endpoints (e.g. `v4-workspaces ls` which is not workspace-scoped) call `v4_get`/`v4_update`/`v4_delete` directly.
- **D-09:** All commands are additive — zero modifications to any existing file.
- **D-10:** All output uses `tools.print_json()`. No custom formatters or table output.
- **D-11:** All errors raised as `CliException`.

### Claude's Discretion
- Exact polling interval and max-wait timeout for `--wait` and `logs` streaming (no user requirement)
- Whether `v4-workspaces ls` injects workspaceId or not (workspace listing is not workspace-scoped — use `v4_get` path without workspace injection)
- Internal structure of the `--wait` polling loop (while loop vs helper function)
- Whether `create` returns the full execution JSON or just the ID when `--wait` is not set

</decisions>

<specifics>
## Specific Ideas

- The `--wait` exit code behavior mirrors CI expectations: scripts can do `neoload v4-test-executions create --test-id X --wait && echo "passed"` without parsing JSON.
- `logs` streaming with offset follows the same conceptual pattern as the existing `neoload logs` command — check that command's implementation for the polling loop pattern.
- v4-workspaces commands at the workspace level (create, delete, get by ID) are not workspace-scoped themselves — they don't need workspaceId injection. Only workspace-member operations may be scoped.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 output (foundation this phase builds on)
- `neoload/neoload_cli_lib/v4/v4_endpoints.py` — `v4_endpoint()`, `v4_workspace_params()`, `v4_inject_workspace()`; all Phase 2 commands use these
- `neoload/neoload_cli_lib/v4/v4_client.py` — `v4_list`, `v4_get`, `v4_create`, `v4_update`, `v4_replace`, `v4_delete`; Phase 2 commands call only these, not rest_crud directly

### Existing command patterns to follow
- `neoload/commands/test_settings.py` — canonical example of `click.Choice` argument pattern, `--file` + named flags pattern, error handling, `tools.print_json()` output
- `neoload/commands/workspaces.py` — simpler example (ls + use only) showing the same pattern
- `neoload/commands/logs.py` — polling/streaming pattern to follow for `v4-test-executions logs`

### v4 API specs (endpoint details, field names, required fields)
- `/Users/m.zimmerman/projects/neoload/nlweb-bench-runtime/rest/src/main/resources/nlweb-bench-runtime-rest.yaml` — test-executions and results/logs v4 endpoints (primary ref for Phase 2)
- `/Users/m.zimmerman/projects/neoload/nlweb-api-router/verticle/src/test/resources/com/neotys/nlweb/api/router/v4/swaggerMerged.yaml` — merged v4 OpenAPI spec; canonical response shapes and pagination model

### CLI infrastructure
- `neoload/neoload_cli_lib/rest_crud.py` — `get`, `post`, `put`, `patch`, `delete` signatures
- `neoload/neoload_cli_lib/user_data.py` — `get_meta`, `set_meta`, `get_meta_required`
- `neoload/neoload_cli_lib/cli_exception.py` — `CliException`
- `neoload/neoload_cli_lib/tools.py` — `print_json`, `is_id`, `ls`

### Test patterns
- `tests/conftest.py` — `neoload_login` fixture; all v4 tests must use `@pytest.mark.usefixtures("neoload_login")`
- `tests/neoload_cli_lib/test_rest_crud.py` — `monkeypatch.setattr(rest_crud, method, lambda ...)` pattern
- `tests/helpers/test_utils.py` — `mock_api_get`, `mock_api_post`, `mock_api_patch`, `mock_api_delete_raw`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `v4_client.v4_list` — use for all `ls` subcommands on workspace-scoped resources (tests, results, zones)
- `v4_client.v4_get` — use for all single-resource fetches by ID
- `v4_client.v4_create` — use for all `create` subcommands (auto-injects workspaceId)
- `v4_client.v4_update` — use for all `patch` subcommands
- `v4_client.v4_delete` — use for all `delete` subcommands; returns None on 204
- `tools.print_json()` — output for all commands

### Established Patterns
- All existing commands call `rest_crud.set_current_command()` and `rest_crud.set_current_sub_command(command)` at the start of the function
- Commands check `if not command: print("command is mandatory..."); return` before dispatch
- `--file` option is typed as `click.File('r')` and the file content is `json.load(file)`
- Named flags that are `None` are excluded from the body dict before merging

### Integration Points
- Command files in `neoload/commands/v4_*.py` are auto-discovered by the filename prefix convention — no changes to `__main__.py`
- Import path for v4 helpers: `from neoload_cli_lib.v4 import v4_client, v4_endpoints`

</code_context>

<deferred>
## Deferred Ideas

- v4 name resolver (lookup by name, not just ID) — deferred; ID-only is sufficient for Phase 2; can be added as a follow-on if users request it
- Live test monitoring / SLA fastfail during `--wait` — the existing `neoload run` has SLA monitoring hooks; v4 equivalent deferred to a later phase
- Log streaming until testExecution reaches terminal status (following executionId instead of polling indefinitely) — deferred; poll-until-empty is sufficient for now

</deferred>

---

*Phase: 02-core-resources*
*Context gathered: 2026-04-09*
