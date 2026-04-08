# Coding Conventions

**Analysis Date:** 2026-04-08

## Naming Patterns

**Files:**
- Source modules: `snake_case.py` (e.g., `rest_crud.py`, `user_data.py`, `docker_lib.py`)
- Command files map directly to CLI subcommands; hyphens in CLI names become underscores in filenames (e.g., `test-settings` → `test_settings.py`)
- Test files: `test_<module>.py` or `test_<feature>.py`
- One exception: `neoLoad_project.py` uses mixed case (inconsistent with rest of codebase)

**Classes:**
- PascalCase: `CliException`, `UserData`, `NeoLoadCLI`, `Resolver`
- Test classes are PascalCase with `Test` prefix: `TestLogin`, `TestLs`, `TestCreate`

**Functions:**
- `snake_case` for all functions: `get_with_pagination`, `parse_filter_spec`, `mock_api_get`
- Private module-level functions prefixed with `__`: `__create_url`, `__handle_error`, `__fill_map`
- Private instance methods prefixed with `__`: `__fill_map`, `__endpoint`

**Variables:**
- `snake_case` for local variables and parameters
- Private module-level singletons prefixed with `__`: `__current_command`, `__no_write`, `__conf_name`
- Constants: lowercase with `__` prefix at module level (no ALL_CAPS convention used)

**CLI Options:**
- Hyphenated in CLI (e.g., `--out-file`, `--as-code`, `--web-vu`)
- Mapped to `snake_case` Python param via `@click.option(..., 'param_name')`

## Code Style

**Formatting:**
- No formatter (no `.prettierrc`, no `black` config, no `autopep8` config detected)
- 4-space indentation (standard Python)
- Strings: single quotes preferred for code, double quotes in f-strings and JSON

**Linting:**
- No linter config detected (no `.flake8`, no `pyproject.toml`, no `pylintrc`)
- SonarCloud used for code quality scanning via `sonar-project.properties`

## Import Organization

**Order (observed pattern):**
1. Standard library imports (`import os`, `import re`, `import sys`, `import json`)
2. Third-party imports (`import click`, `import requests`, `import yaml`)
3. Internal library imports (`from neoload_cli_lib import rest_crud, user_data, tools`)
4. Local command imports (`from commands import test_results`)

**No path aliases used** — imports are relative to `PYTHONPATH="neoload"` set at runtime.

Test files add `sys.path.append('neoload')` in `conftest.py` and import commands directly:
```python
from commands.login import cli as login
from commands.test_settings import cli as settings
```

## Module-Level Private State

Commands and lib modules use module-level private variables for state (singletons, caches):
```python
# neoload/neoload_cli_lib/rest_crud.py
__current_command = ""
__current_sub_command = ""
__agents_already_sent = set()

# neoload/neoload_cli_lib/user_data.py
__no_write = False
__yaml_schema_singleton = __load_yaml_schema()
```

This pattern is used throughout instead of class-based state management.

## CLI Command Pattern

Every command file exposes a `cli` function decorated with `@click.command()`:
```python
# neoload/commands/login.py
@click.command()
@click.option('--url', default="...", help="...", metavar='URL')
@click.argument('token', required=False)
def cli(token, url, no_write, workspace, ssl_cert, local_conf):
    """Docstring shown in --help"""
    rest_crud.set_current_command()
    ...
```

Every `cli` function calls `rest_crud.set_current_command()` as its first statement for user-agent tracking.

Commands that support subcommands use `click.Choice` for the subcommand argument:
```python
# neoload/commands/workspaces.py
@click.argument('command', type=click.Choice(['ls', 'use'], case_sensitive=False), required=False)
```

## Error Handling

**Strategy:** Raise `CliException` (extends `click.ClickException`) for all user-facing errors. This causes Click to print "Error: <message>" and exit with code 1.

```python
# neoload/neoload_cli_lib/cli_exception.py
class CliException(click.ClickException):
    def __init__(self, message):
        super().__init__(message)
    def format_message(self):
        __message = super().format_message()
        if CliException.__debug:
            __message = traceback.format_exc() + "\n\n" + __message
        return __message
```

**HTTP Error Handling** (in `neoload/neoload_cli_lib/rest_crud.py`):
```python
def __handle_error(response):
    if status_code > 299:
        if status_code == 401:
            raise cli_exception.CliException("Server has returned 401 Access denied...")
        else:
            raise cli_exception.CliException("Error " + str(status_code) + " during the request: ...")
    return response
```

**Exception wrapping at top level** (`neoload/__main__.py`):
```python
if __name__ == '__main__':
    try:
        cli()
    except CliException as ex:
        print(ex.format_message(), file=sys.stderr)
    except Exception as ex:
        if cli_exception.CliException.is_debug():
            raise ex
        else:
            print(ex.__str__(), file=sys.stderr)
```

**`pytest.raises` pattern** for tests expecting exceptions:
```python
with pytest.raises(Exception) as context:
    user_data.do_login(None, 'some url', False)
assert 'token is mandatory.' in str(context.value)
```

## Logging

**Framework:** Python standard `logging` module + `coloredlogs` for colored output.

**Patterns:**
- `logging.debug(f'POST {endpoint} body={data}')` — debug-level for HTTP request logging
- `logging.getLogger().warning(f'WARNING: ...')` — warning level for rate-limit and deprecation messages
- Debug logging enabled by `--debug` flag at CLI entry: `logging.getLogger().setLevel(logging.DEBUG)`
- `print()` used directly for user-facing output (not logging)

## Comments

**When to Comment:**
- Explain non-obvious decisions, workarounds, or API quirks
- Multi-line `#` comments before function groups or tricky logic

```python
# Sorry for that, post data are in the query string :'( :'(
# neoload/commands/run.py

# Overrides parse_retry_after
# neoload/neoload_cli_lib/rest_crud.py
```

**Docstrings:**
- Used only on `@click.command` `cli` functions (shown in `--help` output)
- Library functions rarely have docstrings; exceptions are `filtering.py`'s public functions

## Function Design

**Size:** Functions are generally small and focused. `report.py` is the outlier at 1198 lines and contains many embedded helper functions.

**Parameters:** Positional-style; long parameter lists accepted for Click commands (delegated from Click decorators).

**Return Values:**
- Functions returning API data return dicts/lists directly (parsed JSON)
- Void functions raise `CliException` on failure rather than returning error codes
- Boolean helpers follow `is_` prefix: `is_id()`, `is_batch()`, `is_mongodb_id()`

## Module Design

**Exports:**
- No explicit `__all__` declarations; all public functions are implicitly exported
- Wildcard imports used in test files: `from tests.helpers.test_utils import *`

**Resolver Pattern:**
Each command module that operates on named resources defines a module-level `__resolver` and `meta_key`:
```python
# neoload/commands/workspaces.py
__endpoint = "/workspaces"
meta_key = 'workspace id'
__resolver = Resolver(__endpoint, rest_crud.base_endpoint, meta_key)
```

**Singleton via class static method** (used in `UserData`):
```python
class UserData:
    __instance = None

    @staticmethod
    def get_instance():
        if UserData.__instance is None and os.path.exists(CONFIG_FILE):
            ...
        return UserData.__instance
```

---

*Convention analysis: 2026-04-08*
