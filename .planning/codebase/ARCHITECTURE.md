# Architecture

**Analysis Date:** 2026-04-08

## Pattern Overview

**Overall:** Plugin-based CLI with layered library support

**Key Characteristics:**
- Commands are discovered dynamically at runtime from the `neoload/commands/` directory — no static registration required
- A thin command layer delegates all business logic to a shared library layer (`neoload_cli_lib`)
- All external communication goes through a single HTTP abstraction (`rest_crud.py`)
- Session state (login, current workspace, current test settings, current result ID) is persisted to a YAML config file via `user_data.py`
- Commands can be chained on the CLI (Click `chain=True`) to form pipelines

## Layers

**Entry Point:**
- Purpose: Bootstraps the CLI, sets up logging and color output, handles top-level exceptions
- Location: `neoload/__main__.py`
- Contains: `NeoLoadCLI` (custom `click.Group`) with dynamic command discovery, top-level `cli` function
- Depends on: `neoload_cli_lib.tools`, `neoload_cli_lib.cli_exception`
- Used by: `console_scripts` entry point `neoload` (defined in `setup.py`)

**Commands Layer:**
- Purpose: Parse CLI arguments and options, delegate to library functions, print results
- Location: `neoload/commands/*.py`
- Contains: One `cli` Click command per file; each file maps to one CLI subcommand
- Depends on: `neoload_cli_lib` modules; sibling command modules (e.g., `run.py` imports `test_settings`, `test_results`)
- Used by: `NeoLoadCLI.get_command()` which `eval()`s the file by name

**Library Layer (`neoload_cli_lib`):**
- Purpose: Shared business logic, HTTP communication, state management, output formatting
- Location: `neoload/neoload_cli_lib/*.py`
- Contains: REST client, user session, name resolution, hooks, schema validation, Docker integration, output display
- Depends on: External packages (`requests`, `click`, `yaml`, `jinja2`, `docker`, etc.)
- Used by: Commands layer

**Resource Layer:**
- Purpose: Jinja2 templates for report generation
- Location: `neoload/resources/jinja/`
- Contains: Built-in report templates (`.j2` files) for single-run and trend reports; shared CSS and JS
- Depends on: Nothing at runtime (loaded by `report.py` via `importlib-resources`)
- Used by: `neoload/commands/report.py`

## Data Flow

**Typical Command Execution:**

1. User invokes `neoload <subcommand> [args]`
2. `NeoLoadCLI.get_command()` in `neoload/__main__.py` finds and `eval()`s `neoload/commands/<subcommand>.py`
3. The command's `cli()` function calls `rest_crud.set_current_command()` to track the current command for User-Agent headers
4. Command resolves any name-to-ID translation via `Resolver` in `neoload_cli_lib/name_resolver.py`, which calls `rest_crud.get_with_pagination()` to list remote entities
5. Command calls `rest_crud.get/post/put/patch/delete()` with the resolved endpoint
6. `rest_crud` reads auth token and URL from the `UserData` singleton via `user_data.get_user_data()`
7. HTTP response is returned as parsed JSON; command prints via `tools.print_json()` or `displayer`
8. Command stores the "current" entity ID in session metadata via `user_data.set_meta(meta_key, id)`

**Test Run Flow:**

1. `neoload run` resolves test settings name/ID
2. POSTs to `/tests/{id}/start` to create a test result; stores result ID in session
3. Unless `--detached`, delegates to `running_tools.wait()` which polls `rest_crud.get()` on the result endpoint in a 1-second loop
4. During RUNNING status, prints live statistics and log entries
5. On SIGINT, prompts user to stop the test gracefully or forcefully via `running_tools.stop()`
6. On TERMINATED, calls `test_results.summary()` and exits with SLA-based exit code

**Session State Flow:**

1. `neoload login` calls `user_data.do_login()`, which creates a `UserData` singleton
2. `UserData` is serialized to YAML at `~/.local/share/neoload-cli/1.0/config.yaml` (or `.neoload_cli.yaml` if local flag used)
3. Subsequent commands call `user_data.get_user_data()` which lazy-loads `UserData` from the YAML file
4. `user_data.set_meta(key, value)` / `user_data.get_meta(key)` read/write the `metadata` dict inside `UserData` and re-serialize to disk immediately

**Report Generation Flow:**

1. `neoload report` fetches statistics, SLA, elements, and events from multiple REST endpoints (optionally in parallel via `concurrent.futures`)
2. Assembles a JSON model in memory
3. Renders the model through a Jinja2 template (built-in from `neoload/resources/jinja/` or user-supplied path)
4. Writes output to file or stdout

## Key Abstractions

**`NeoLoadCLI` (dynamic plugin loader):**
- Purpose: Discovers and loads command modules at runtime without a static registry
- Location: `neoload/__main__.py`
- Pattern: Overrides `click.Group.list_commands()` and `get_command()`; maps filename → subcommand name (underscores become hyphens)

**`UserData` (singleton session):**
- Purpose: Holds auth token, API URL, file storage URL, NLW version, and arbitrary metadata (current workspace/test-settings/result IDs)
- Location: `neoload/neoload_cli_lib/user_data.py`
- Pattern: Singleton via `UserData.__instance`; persisted to YAML on every `set_meta()` call

**`Resolver` (lazy name-to-ID cache):**
- Purpose: Translates human-readable entity names to API UUIDs, with workspace-scoped in-memory caching
- Location: `neoload/neoload_cli_lib/name_resolver.py`
- Pattern: Each command module instantiates its own `Resolver` with its endpoint, a `base_endpoint` callable, and a `meta_key`; the cache is populated lazily on first name lookup

**`rest_crud` (HTTP abstraction):**
- Purpose: Provides `get/post/put/patch/delete` + pagination + binary upload over a shared `requests.Session` with retry logic (rate-limit aware)
- Location: `neoload/neoload_cli_lib/rest_crud.py`
- Pattern: Module-level session with retry adapter; all methods inject auth headers and handle HTTP error codes uniformly

**`hooks` (event system):**
- Purpose: Allows optional modules (e.g., `docker_lib`) to register callbacks that fire on lifecycle events (`test.start`, `test.stop`)
- Location: `neoload/neoload_cli_lib/hooks.py`
- Pattern: Hook names and callback function paths stored in `config_global`; triggered via dynamic import + `getattr` traversal

**`config_global` (persistent key-value store):**
- Purpose: Stores user preferences and hook registrations that survive across login/logout cycles
- Location: `neoload/neoload_cli_lib/config_global.py`
- Pattern: In-memory dict backed by YAML file at `~/.local/share/neoload-cli/1.0/config-global.yaml`; auto-saves on every `set_attr()` call

## Entry Points

**CLI Entry Point:**
- Location: `neoload/__main__.py`
- Triggers: `neoload` console script (via `setup.py` `entry_points`)
- Responsibilities: Configure logging/color, parse global `--debug`/`--batch` flags, route to subcommand

**Command Modules (one per subcommand):**
- Locations: `neoload/commands/config.py`, `neoload/commands/login.py`, `neoload/commands/logout.py`, `neoload/commands/project.py`, `neoload/commands/report.py`, `neoload/commands/run.py`, `neoload/commands/status.py`, `neoload/commands/stop.py`, `neoload/commands/test_results.py`, `neoload/commands/test_settings.py`, `neoload/commands/validate.py`, `neoload/commands/wait.py`, `neoload/commands/workspaces.py`, `neoload/commands/zones.py`, `neoload/commands/docker.py`, `neoload/commands/fastfail.py`, `neoload/commands/logs.py`, `neoload/commands/logs_url.py`
- Triggers: Dynamic `eval()` by `NeoLoadCLI.get_command()`
- Responsibilities: Parse options/arguments, validate inputs, delegate to `neoload_cli_lib`, set session state

## Error Handling

**Strategy:** All errors are raised as `CliException` (a subclass of `click.ClickException`) and caught at the top level in `__main__.py`; exit code is non-zero; message printed to stderr.

**Patterns:**
- `rest_crud.__handle_error()` raises `CliException` for any HTTP status > 299; 401 gets a specific message about token validity
- Commands raise `CliException` for bad inputs (invalid JSON, missing required state, unresolvable names)
- `--debug` flag causes `CliException.format_message()` to prepend the full traceback
- In non-debug mode, bare `Exception` is also caught at the top level and printed to stderr without traceback

## Cross-Cutting Concerns

**Logging:** Python `logging` module; level set to DEBUG when `--debug` flag is passed; `coloredlogs` applies colored formatting on color-capable terminals.

**Validation:** As-code YAML files are validated against a remote JSON Schema (fetched from GitHub, cached on disk at `~/.local/share/neoload-cli/1.0/yaml_schema.json`); implemented in `neoload_cli_lib/schema_validation.py`.

**Authentication:** Bearer-token style; token stored in `UserData.token` and injected as `accountToken` header on every request by `rest_crud.__create_additional_headers()`. No OAuth flow; token is provided directly by the user at `neoload login`.

**Versioning:** NeoLoad Web server version is fetched at login and stored in `UserData.metadata['version']`; `user_data.is_version_lower_than(v)` guards version-specific behavior throughout the codebase.

**Workspace scoping:** `rest_crud.base_endpoint_with_workspace()` returns either `v2` or `v3/workspaces/{id}` depending on stored workspace ID, transparently injected into all API endpoint paths.

---

*Architecture analysis: 2026-04-08*
