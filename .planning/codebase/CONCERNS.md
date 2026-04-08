# Codebase Concerns

**Analysis Date:** 2026-04-08

## Tech Debt

**Dynamic command loading via eval/exec:**
- Issue: `__main__.py` loads CLI commands by reading `.py` files off disk, compiling them, and calling `eval(code, ns, ns)` at runtime. This is fragile, bypasses normal Python import machinery, and makes static analysis impossible.
- Files: `neoload/__main__.py` lines 34-39
- Impact: Refactoring or renaming command files breaks the CLI silently. IDEs and type checkers cannot resolve the code path. Risks executing arbitrary `.py` files dropped into the commands folder.
- Fix approach: Use a normal Python package with explicit imports or Click's `add_command` pattern.

**POST body sent as query string in run command:**
- Issue: Test run parameters (name, description, as-code, VU counts, etc.) are sent as URL query string parameters rather than as a JSON body. This is acknowledged with an apology comment.
- Files: `neoload/commands/run.py` line 52-55, `create_data()` function lines 75-92
- Impact: Query string length limits could silently truncate parameters. Sensitive data (test names, descriptions) appears in server access logs and HTTP proxy logs.
- Fix approach: Refactor to send parameters in the POST body once the API supports it.

**Hardcoded 5-second sleep after test start:**
- Issue: A `time.sleep(5)` call exists after the POST that starts a test run, described as "Wait 5 seconds until the test result is created."
- Files: `neoload/commands/run.py` line 59
- Impact: Slow CI pipelines. If the API is slower than 5 seconds (network latency), subsequent PATCH calls fail silently.
- Fix approach: Poll the test result endpoint with a timeout instead of sleeping blindly.

**Hardcoded 4-hour maximum fastfail loop duration:**
- Issue: `get_duration_mins_by_result()` returns a hardcoded `(60 * 4)` minutes as the worst-case run duration. The commented-out TODO block explains this should be derived from the actual project definition.
- Files: `neoload/commands/fastfail.py` lines 129-136, TODO comments at lines 101 and 180
- Impact: Tests running longer than 4 hours will have fastfail exit prematurely. Tests shorter than 4 hours will always run the loop up to the full time budget even after exit conditions are met.
- Fix approach: Implement the commented-out logic to fetch scenario duration from the project metadata.

**Project upload: no pre-validation before upload:**
- Issue: Four sequential TODO comments acknowledge that upload should pre-validate YAML with the `validate` command, recurse through includes, and deduplicate files. None of this is implemented.
- Files: `neoload/commands/project.py` lines 56-59
- Impact: Invalid projects are uploaded and only fail on server-side, giving poor error messages with no file reference.
- Fix approach: Integrate `schema_validation.validate_yaml_dir` before zipping and uploading.

**Deprecated --cirix-vu option retained indefinitely:**
- Issue: The `--cirix-vu` flag (misspelling of `--citrix-vu`) is kept as a hidden option that still works but prints a deprecation warning. There is no removal plan or version indicator.
- Files: `neoload/commands/run.py` lines 19, 85-87
- Impact: Dead code maintained forever; confusing if users encounter it in scripts.
- Fix approach: Remove in a future major version with a migration note.

**Version compatibility shims accumulating:**
- Issue: Multiple `is_version_lower_than()` checks for versions as old as `2.5.0` and `2.6.0` exist throughout the codebase, implying NLW servers older than 4+ years are still supported.
- Files: `neoload/neoload_cli_lib/rest_crud.py` lines 56, 64; `neoload/commands/run.py` line 108; `neoload/commands/test_results.py` lines 113, 133; `neoload/commands/login.py` line 31; `neoload/commands/report.py` line 259; `neoload/commands/workspaces.py` line 23
- Impact: Code paths diverge on every API call, increasing testing complexity. The `v2`/`v3` endpoint branching makes reasoning about behavior difficult.
- Fix approach: Establish a minimum supported NLW version and remove legacy branches.

**Global mutable state across modules:**
- Issue: Many modules use module-level `global` statements for shared state: `__current_command`, `__current_sub_command`, `__agents_already_sent` in `rest_crud.py`; `__current_id`, `__count`, `nbsecond`, `__last_status` in `running_tools.py`; `__batch` in `tools.py`; singleton `client` in `docker_lib.py`.
- Files: `neoload/neoload_cli_lib/rest_crud.py`, `neoload/neoload_cli_lib/running_tools.py`, `neoload/neoload_cli_lib/tools.py`, `neoload/neoload_cli_lib/docker_lib.py`
- Impact: State leaks between chained CLI commands (Click supports chaining). Concurrent execution in tests requires careful reset. No thread-safety in `running_tools.py` counters.
- Fix approach: Pass state explicitly through function parameters or a context object.

**report.py is a 1,198-line monolith:**
- Issue: The report command is a single file containing CLI parsing, data fetching, data transformation, output formatting, Jinja rendering, thread pool management, and filter parsing.
- Files: `neoload/commands/report.py`
- Impact: Extremely difficult to test individual concerns in isolation. Tests must mock many unrelated parts. Changes in one area easily break another.
- Fix approach: Extract into separate modules: data fetcher, filter parser, template renderer, output writer.

---

## Security Considerations

**API token stored in plaintext on disk:**
- Risk: The authentication token is persisted to `~/.local/share/neoload-cli/neotys/1.0/config.yaml` (or `.neoload_cli.yaml`) via `yaml.dump(instance.__dict__, stream)` — completely plaintext, including the token field.
- Files: `neoload/neoload_cli_lib/user_data.py` lines 181-188
- Current mitigation: None. The `__str__` method masks the token for display, but the file write uses `__dict__` directly.
- Recommendations: Use OS keychain/secret store (e.g., `keyring` library) or at minimum restrict file permissions with `os.chmod(dest_file, 0o600)` after writing.

**API token passed as Docker environment variable:**
- Risk: The NeoLoad Web token is passed directly into container environment variables, which are visible to any process in the container and appear in `docker inspect` output.
- Files: `neoload/neoload_cli_lib/docker_lib.py` line 180
- Current mitigation: None.
- Recommendations: Use Docker secrets mount or a short-lived token scoped to the test run.

**urllib3 warnings disabled globally:**
- Risk: `urllib3.disable_warnings()` is called unconditionally at startup. This silences SSL certificate verification warnings, meaning users with `--ssl-cert False` receive no warning that their connection is unverified.
- Files: `neoload/__main__.py` line 13
- Current mitigation: None.
- Recommendations: Only disable warnings if `--ssl-cert False` is explicitly passed.

**shell=True in subprocess call:**
- Risk: The `--stop-command` option is executed with `subprocess.run(stop_command, shell=True, ...)`. The command string comes from CLI user input and is passed directly to the shell.
- Files: `neoload/commands/fastfail.py` line 154
- Current mitigation: The value comes from the user's own command line, so the risk is self-inflicted in interactive use. In CI pipelines where the value comes from environment variables or untrusted config, this is a shell injection vector.
- Recommendations: Parse the command into a list and use `shell=False`, or document that only trusted input should be used.

**eval() call in displayer for colorama lookups:**
- Risk: `eval("colorama." + key)` is called where `key` is derived from `colorama.Fore.__dict__.keys()` and `colorama.Back.__dict__.keys()`. While the source is internal, it establishes a pattern that is risky if the data source ever changes.
- Files: `neoload/neoload_cli_lib/displayer.py` line 160
- Current mitigation: Input is currently controlled (colorama enum keys).
- Recommendations: Replace with `getattr(colorama, key)` which is safe and explicit.

**Access token exposed in HTTP request logs when debug is enabled:**
- Risk: When `--debug` is passed, `urllib3` request logging is set to DEBUG level and propagated. HTTP headers (including `accountToken`) are logged to stdout.
- Files: `neoload/__main__.py` lines 52-54; `neoload/neoload_cli_lib/rest_crud.py` lines 187-193
- Current mitigation: Only active in debug mode.
- Recommendations: Sanitize headers in debug output, or document this behavior prominently.

---

## Fragile Areas

**Jinja template rendering with autoescape enabled on all output types:**
- Files: `neoload/commands/report.py` lines 230-234
- Why fragile: `jinja2.Environment(autoescape=True)` is set for all templates including CSV output. HTML autoescaping will corrupt CSV output containing characters like `&`, `<`, `>`. This may already be producing incorrect CSV in some cases.
- Safe modification: Use `autoescape=False` for non-HTML templates or set `autoescape` based on template file extension.
- Test coverage: Tests exist for CSV templates but may not test data containing HTML-special characters.

**Pagination termination relies on first-element comparison:**
- Files: `neoload/neoload_cli_lib/rest_crud.py` lines 78-83
- Why fragile: The pagination loop breaks if `all_entities[0] == entities[0]`, used to detect non-paginated endpoints that return the same page regardless of offset. This will silently truncate results if the first entity genuinely repeats across pages in a large dataset, or incorrectly stop if the API returns sorted results and the top item changes between calls.
- Safe modification: Use a response header (`X-Total-Count` or similar) if the API provides one, or compare full pages rather than first elements.
- Test coverage: Not directly tested.

**UserData loaded via `__dict__.update(desc)` from YAML:**
- Files: `neoload/neoload_cli_lib/user_data.py` lines 121-122
- Why fragile: Loading config by calling `self.__dict__.update(desc)` from an untrusted YAML file means any key in the config file becomes an instance attribute, including Python dunder attributes. A malformed or tampered config file could override internal methods.
- Safe modification: Explicitly map known keys (`token`, `url`, `metadata`, `resolved_ids`, `file`) instead of bulk-updating `__dict__`.

**Hooks system loads arbitrary module strings from disk config:**
- Files: `neoload/neoload_cli_lib/hooks.py` lines 7-20
- Why fragile: Hook function strings are read from `config-global.yaml`, then resolved via `__import__` and `getattr`. A tampered config file can load and execute any importable Python module.
- Safe modification: Restrict allowed hook names to a whitelist of known module paths.

**`tools.__is_color_terminal` accessed as a private name from outside its module:**
- Files: `neoload/neoload_cli_lib/displayer.py` line 4 (import), `neoload/commands/report.py` line 102
- Why fragile: Python name mangling does not apply at module level, so this works, but importing a private name means any internal refactoring of `tools.py` silently breaks callers.
- Safe modification: Expose `is_color_terminal()` (the public version already exists) and use that instead.

---

## Performance Bottlenecks

**Sequential API calls for report data fetching:**
- Problem: `get_single_report` makes up to 9 sequential REST calls to fill report data (summary, SLAs, stats, events, requests, transactions, monitors, ext_data, controller points).
- Files: `neoload/commands/report.py` lines 344-366
- Cause: Each `fill_single_*` function makes a blocking `rest_crud.get()` call. Only the element-level data (`get_elements_data`) is parallelized.
- Improvement path: Parallelize the top-level fill functions using the same `ThreadPoolExecutor` pattern already used for elements.

**`fastfail` polls every 15 seconds with no backoff:**
- Problem: The monitor loop in `fastfail` calls the SLA API every 15 seconds for the entire test duration with no exponential backoff.
- Files: `neoload/commands/fastfail.py` line 95
- Cause: Fixed `time.sleep(15)` in the loop.
- Improvement path: Increase poll interval during the INIT phase when SLA failures are unlikely.

---

## Dependencies at Risk

**`requests.packages.urllib3` direct import:**
- Risk: `from requests.packages.urllib3.util.retry import Retry` uses the bundled urllib3 inside requests. Since requests 2.28+, urllib3 is a separate dependency and `requests.packages` is deprecated.
- Files: `neoload/neoload_cli_lib/rest_crud.py` line 15
- Impact: Will break on future requests versions that drop the bundled re-export.
- Migration plan: Change to `from urllib3.util.retry import Retry`.

**`importlib_resources` fallback for Python < 3.7:**
- Risk: `get_resource_as_string()` has a try/except import block to handle Python 3.6 via the backport `importlib_resources`. Python 3.6 reached end-of-life in December 2021.
- Files: `neoload/commands/report.py` lines 170-178
- Impact: Carrying dead compatibility code. The `importlib_resources` package listed in `setup.py` as a dependency is unnecessary for any currently supported Python.
- Migration plan: Drop the `try/except` import fallback and require Python 3.9+ which has `pkg_resources.files()`.

**`simplejson` used for `JSONDecodeError` only:**
- Risk: `simplejson` is a full JSON library installed solely to import its `JSONDecodeError` in `user_data.py`. The standard library `json.JSONDecodeError` (available since Python 3.5) could replace it entirely.
- Files: `neoload/neoload_cli_lib/user_data.py` line 8; `setup.py` line 48
- Impact: Unnecessary dependency adding installation weight.
- Migration plan: Replace `from simplejson import JSONDecodeError` with `from json import JSONDecodeError`.

---

## Test Coverage Gaps

**`status.py`, `stop.py`, `workspaces.py`, `test_results.py`, `test_settings.py` have no direct unit tests:**
- What's not tested: The `status`, `stop`, `workspaces`, `test_results`, and `test_settings` command files have no corresponding test file (confirmed by file name search).
- Files: `neoload/commands/status.py`, `neoload/commands/stop.py`, `neoload/commands/workspaces.py`, `neoload/commands/test_results.py`, `neoload/commands/test_settings.py`
- Risk: Regressions in these commands go undetected. Note: `test_settings` sub-operations (create, patch, put, ls, delete) have tests, but the top-level command dispatch does not.
- Priority: High for `stop.py` and `test_results.py` as they are used in CI pipelines.

**`project.py` has no direct unit test:**
- What's not tested: The upload dispatch logic in `project.py` (path detection, zip vs file vs folder routing, password detection triggering the URL message) is not covered. `test_upload.py` and `test_upload_with_password.py` exist but test the underlying `neoLoad_project` library functions, not the CLI command itself.
- Files: `neoload/commands/project.py`
- Risk: Changes to upload routing logic are undetected.
- Priority: Medium.

**`fastfail` monitor loop is not unit tested:**
- What's not tested: The `monitor_loop`, `process_state`, `monitor_loop_check`, and `get_duration_mins_by_result` functions in `fastfail.py` have no test coverage. `test_fastfail_slas.py` exists but covers only SLA data retrieval, not the polling loop behavior.
- Files: `neoload/commands/fastfail.py`
- Risk: Loop exit conditions, exit code computation, and stop-command execution are untested.
- Priority: High.

**Pagination edge cases in `rest_crud.get_with_pagination` are untested:**
- What's not tested: The first-element duplicate detection break logic, behavior when total count is exactly equal to `page_size`, and behavior when `page_size` does not divide evenly into total results.
- Files: `neoload/neoload_cli_lib/rest_crud.py` lines 67-86
- Risk: Silent data truncation in listing commands.
- Priority: Medium.

---

*Concerns audit: 2026-04-08*
