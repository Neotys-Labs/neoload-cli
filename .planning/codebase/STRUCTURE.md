# Codebase Structure

**Analysis Date:** 2026-04-08

## Directory Layout

```
neoload-cli/
├── neoload/                    # Main package
│   ├── __main__.py             # CLI entry point; dynamic command loader
│   ├── commands/               # One file per CLI subcommand
│   │   ├── config.py           # neoload config
│   │   ├── docker.py           # neoload docker
│   │   ├── fastfail.py         # neoload fastfail
│   │   ├── login.py            # neoload login
│   │   ├── logout.py           # neoload logout
│   │   ├── logs.py             # neoload logs
│   │   ├── logs_url.py         # neoload logs-url
│   │   ├── project.py          # neoload project
│   │   ├── report.py           # neoload report
│   │   ├── run.py              # neoload run
│   │   ├── status.py           # neoload status
│   │   ├── stop.py             # neoload stop
│   │   ├── test_results.py     # neoload test-results
│   │   ├── test_settings.py    # neoload test-settings
│   │   ├── validate.py         # neoload validate
│   │   ├── wait.py             # neoload wait
│   │   ├── workspaces.py       # neoload workspaces
│   │   └── zones.py            # neoload zones
│   ├── neoload_cli_lib/        # Shared library modules
│   │   ├── bad_as_code_exception.py
│   │   ├── cli_exception.py    # CliException (extends ClickException)
│   │   ├── config_global.py    # Persistent key-value config store
│   │   ├── displayer.py        # SLA display and JUnit XML output
│   │   ├── docker_lib.py       # Docker daemon integration
│   │   ├── filtering.py        # Filter-spec parser for ls commands
│   │   ├── hooks.py            # Lifecycle event hook system
│   │   ├── logs_tools.py       # Log line fetching and display
│   │   ├── logs_traduction_map.py  # Log message translation table
│   │   ├── name_resolver.py    # Name-to-ID resolution with caching
│   │   ├── neoLoad_project.py  # Project zip/upload logic
│   │   ├── paths.py            # appdirs config path helper
│   │   ├── rest_crud.py        # HTTP client (get/post/put/patch/delete)
│   │   ├── running_tools.py    # Test polling loop, stop, statistics display
│   │   ├── schema_validation.py # YAML as-code schema validation
│   │   ├── tools.py            # General utilities (ID regex, confirm, print, CI detection)
│   │   └── user_data.py        # UserData singleton; session persistence
│   └── resources/
│       └── jinja/              # Built-in Jinja2 report templates
│           ├── builtin_console_summary.j2
│           ├── builtin_transactions_csv.j2
│           ├── custom_transactions_export.j2
│           ├── sample-custom-report.html.j2
│           ├── sample-trends-report.html.j2
│           ├── common/         # Shared JS, CSS, partial templates
│           └── trends/         # Trend-specific templates
├── tests/
│   ├── commands/               # Unit tests mirroring neoload/commands/
│   │   ├── docker/
│   │   ├── fastfail/
│   │   ├── project/
│   │   ├── report/
│   │   ├── status/
│   │   ├── test_logs/
│   │   ├── test_results/
│   │   ├── test_settings/      # Split by subcommand (test_create.py, test_ls.py, etc.)
│   │   ├── wait/
│   │   ├── workspaces/
│   │   ├── zones/
│   │   ├── test_config.py
│   │   ├── test_login.py
│   │   ├── test_logout.py
│   │   ├── test_logs_url.py
│   │   ├── test_run.py
│   │   └── test_validate.py
│   ├── helpers/
│   │   └── test_utils.py       # Shared monkeypatch helpers for rest_crud mocking
│   ├── integration/            # Integration/acceptance test scripts
│   │   ├── scripts/
│   │   └── expected/
│   ├── neoload_cli_lib/        # Unit tests for lib modules
│   ├── neoload_projects/       # Sample NeoLoad project fixtures for tests
│   │   └── example_1/
│   └── resources/              # Test fixture files (JSON, Jinja templates)
│       ├── jinja/
│       └── report/
├── examples/
│   ├── docker/                 # Docker Compose examples
│   └── pipelines/              # CI pipeline config examples (GitHub, GitLab, Jenkins, etc.)
├── resources/                  # Top-level static resources (non-package)
├── notes/                      # Developer notes
├── .github/workflows/          # GitHub Actions CI workflows
├── setup.py                    # Package metadata and dependencies
├── pytest.ini                  # Pytest markers and configuration
├── requirements.txt            # Dev/test requirements
├── MANIFEST.in                 # Files to include in source distribution
└── .travis.yml                 # Travis CI configuration
```

## Directory Purposes

**`neoload/commands/`:**
- Purpose: Each `.py` file is one CLI subcommand
- Contains: A single `cli` Click command function; module-level `__endpoint`, `meta_key`, and `__resolver` constants for resource-managing commands
- Key files: `neoload/commands/run.py` (test execution), `neoload/commands/test_settings.py` (CRUD pattern reference), `neoload/commands/report.py` (Jinja templating)

**`neoload/neoload_cli_lib/`:**
- Purpose: All shared logic; commands must not contain business logic directly
- Contains: HTTP client, session management, utilities, hooks, schema validation
- Key files: `neoload/neoload_cli_lib/rest_crud.py`, `neoload/neoload_cli_lib/user_data.py`, `neoload/neoload_cli_lib/name_resolver.py`, `neoload/neoload_cli_lib/running_tools.py`

**`neoload/resources/jinja/`:**
- Purpose: Bundled report templates distributed with the package
- Contains: `.j2` Jinja2 templates; `common/` holds shared partials (JS, CSS, partial HTML); `trends/` holds trend-specific templates
- Generated: No — hand-authored
- Committed: Yes

**`tests/commands/`:**
- Purpose: Unit tests for each command module; structure mirrors `neoload/commands/`
- Contains: Tests use Click's `CliRunner` and monkeypatch `rest_crud` functions via `tests/helpers/test_utils.py`

**`tests/helpers/`:**
- Purpose: Shared test utilities
- Contains: `test_utils.py` — `mock_api_get`, `mock_api_post`, `mock_api_patch`, `mock_api_put`, `mock_api_delete_raw`, `mock_login_get_urls`, `assert_success`

**`tests/neoload_projects/`:**
- Purpose: Sample NeoLoad project file trees used as test fixtures for project upload tests
- Generated: No

**`examples/pipelines/`:**
- Purpose: Reference CI pipeline configurations showing how to use the CLI in various CI systems
- Contains: Sub-directories per CI platform (`github`, `gitlab`, `jenkins`, `bamboo-specs`, `azure_devops`, `aws`)

## Key File Locations

**Entry Points:**
- `neoload/__main__.py`: CLI bootstrap; `NeoLoadCLI` class; top-level `cli` command
- `setup.py`: Declares `neoload=neoload.__main__:cli` console script

**Configuration:**
- `pytest.ini`: Pytest markers for test categorization
- `setup.py`: All package dependencies and versioning (uses `setuptools_scm`)
- `MANIFEST.in`: Ensures Jinja templates are included in sdist

**Core Logic:**
- `neoload/neoload_cli_lib/rest_crud.py`: All HTTP communication
- `neoload/neoload_cli_lib/user_data.py`: Session state and persistence
- `neoload/neoload_cli_lib/name_resolver.py`: Name-to-ID resolution
- `neoload/neoload_cli_lib/running_tools.py`: Test polling and stop logic
- `neoload/neoload_cli_lib/hooks.py`: Lifecycle event hooks

**Testing:**
- `tests/helpers/test_utils.py`: All shared mock helpers
- `tests/commands/`: Per-command unit tests
- `tests/neoload_cli_lib/`: Library unit tests

## Naming Conventions

**Files:**
- Command files: `snake_case.py` matching the CLI subcommand with hyphens replaced by underscores (e.g., `test_settings.py` → `neoload test-settings`)
- Library files: `snake_case.py` (e.g., `rest_crud.py`, `user_data.py`)
- Test files: `test_<subject>.py` prefix (e.g., `test_create.py`, `test_login.py`)

**Directories:**
- Test directories mirror source directories exactly: `tests/commands/test_settings/` mirrors `neoload/commands/test_settings.py`

**Module-level constants in command files:**
- `__endpoint`: API path fragment (e.g., `"/tests"`, `"/workspaces"`)
- `meta_key`: String key used to store the "currently selected" entity ID in `UserData.metadata` (e.g., `'settings id'`, `'result id'`)
- `__resolver`: `Resolver` instance scoped to this command's resource type

**CLI function:**
- Every command file exposes exactly one function named `cli` — this is what `NeoLoadCLI.get_command()` extracts from the `eval()`'d namespace

## Where to Add New Code

**New CLI subcommand:**
- Create `neoload/commands/<name>.py` with a `cli` Click command function
- Add tests in `tests/commands/` (new directory or file matching the command name)
- No registration needed — `NeoLoadCLI` auto-discovers it
- If the command manages a remote resource, follow the pattern in `neoload/commands/test_settings.py`: define `__endpoint`, `meta_key`, `__resolver` at module level

**New library utility:**
- Add to an existing module in `neoload/neoload_cli_lib/` if closely related, or create a new `neoload/neoload_cli_lib/<name>.py`
- Tests go in `tests/neoload_cli_lib/`

**New built-in report template:**
- Add `.j2` file to `neoload/resources/jinja/` (or `common/`/`trends/` subdirectory)
- Register the template name in the `--template` option help text in `neoload/commands/report.py`

**New CI pipeline example:**
- Add config files under `examples/pipelines/<ci-platform>/`

## Special Directories

**`neoload/resources/`:**
- Purpose: Package data distributed with the wheel/sdist
- Generated: No
- Committed: Yes
- Note: Included via `MANIFEST.in` and `include_package_data=True` in `setup.py`; accessed at runtime via `importlib-resources`

**`.planning/`:**
- Purpose: GSD planning documents (architecture maps, phase plans)
- Generated: By GSD tooling
- Committed: Yes

---

*Structure analysis: 2026-04-08*
