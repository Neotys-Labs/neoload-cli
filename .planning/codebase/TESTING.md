# Testing Patterns

**Analysis Date:** 2026-04-08

## Test Framework

**Runner:**
- pytest
- Config: `pytest.ini` (at project root)

**Assertion Library:**
- pytest's built-in `assert`
- No separate assertion library (e.g., no `assertpy`, no `hamcrest`)

**Additional plugins:**
- `pytest-datafiles` — loads fixture files into tests (file upload tests)
- `pytest-mock` — listed in `requirements.txt`
- `click.testing.CliRunner` — used for all CLI command invocation

**Run Commands:**
```bash
PYTHONPATH="neoload" pytest                          # Run all unit/mock tests
PYTHONPATH="neoload" pytest -m "not makelivecalls"   # Run only mocked tests (default in CI)
PYTHONPATH="neoload" pytest -v -x -m "makelivecalls" --makelivecalls --token TOKEN --url URL  # Integration tests
PYTHONPATH="neoload" coverage run -m pytest          # Run with coverage
coverage xml                                         # Generate coverage.xml for SonarCloud
```

**Coverage:**
- Generated with `coverage` (not pytest-cov)
- Report path: `coverage.xml` (consumed by SonarCloud)
- Unit and live-call coverage combined: `coverage combine`

## Test File Organization

**Location:** Separate `tests/` directory (not co-located with source)

**Naming:**
- Files: `test_<feature>.py` or `test_<feature>_<aspect>.py`
- Classes: `Test<Feature>` (e.g., `TestLogin`, `TestCreate`, `TestLs`)
- Methods: `test_<scenario>` (e.g., `test_login_basic`, `test_list_all`, `test_error_not_logged_in`)

**Structure:**
```
tests/
├── conftest.py                     # Shared fixtures and session setup
├── helpers/
│   ├── __init__.py
│   └── test_utils.py               # Shared mock helpers (mock_api_get, assert_success, etc.)
├── resources/                      # Expected output files for snapshot tests
│   ├── expected_summary_text_no_sla.txt
│   ├── expected_summary_text_with_sla.txt
│   ├── expected_neoload_junit_slas.xml
│   └── jinja/
├── neoload_projects/               # Sample NLP project files for upload tests
│   └── example_1.zip
├── neoload_cli_lib/                # Unit tests for library modules
│   ├── test_displayer.py
│   ├── test_filtering.py
│   ├── test_rest_crud.py
│   ├── test_running_tools.py
│   ├── test_SchemaValidation.py
│   ├── test_tools.py
│   └── test_user_data.py
├── commands/                       # Integration/command tests
│   ├── test_login.py
│   ├── test_logout.py
│   ├── test_run.py
│   ├── test_config.py
│   ├── test_validate.py
│   ├── test_logs_url.py
│   ├── test_settings/
│   │   ├── test_ls.py
│   │   ├── test_create.py
│   │   ├── test_patch.py
│   │   ├── test_put.py
│   │   ├── test_delete.py
│   │   └── test_createorpatch.py
│   ├── test_results/
│   ├── report/
│   ├── project/
│   ├── workspaces/
│   ├── zones/
│   ├── status/
│   ├── wait/
│   ├── fastfail/
│   ├── test_logs/
│   └── docker/
└── test_readme.py                  # Acceptance tests validating README examples
```

## Test Structure

**Class-based suite organization (most common):**
```python
@pytest.mark.settings
@pytest.mark.usefixtures("neoload_login")
class TestLs:
    def test_list_all(self, monkeypatch):
        runner = CliRunner()
        mock_api_get_with_pagination(monkeypatch, 'v2/tests', '[{"id":"someId", ...}]')
        result_ls = runner.invoke(settings, ['ls'])
        assert_success(result_ls)
        json_result = json.loads(result_ls.output)
        assert json_result[0]['id'] is not None
```

**Module-level functions (less common, for pure unit tests):**
```python
# tests/neoload_cli_lib/test_tools.py
def test_string_to_boolean_json():
    for true_value in tools.get_true_values():
        assert string_to_bool_json(true_value) is True
```

**Patterns:**
- Session setup: `pytest_sessionstart` in `conftest.py` runs `login` with a bad URL to initialize the command class
- Per-test setup: `@pytest.mark.usefixtures("neoload_login")` on the class
- No `setUp`/`tearDown` or `setup_method`/`teardown_method` used

## Mocking

**Framework:** pytest's `monkeypatch` fixture (built-in) — NOT `pytest-mock`'s `mocker`

**Primary mocking strategy:** Patch functions on the `rest_crud` module directly via `monkeypatch.setattr`.

All REST mocking is centralized in `tests/helpers/test_utils.py`:

```python
def mock_api_get(monkeypatch, endpoint, json_result):
    __mock_api_without_data(monkeypatch, 'get', endpoint, json_result)

def mock_api_post(monkeypatch, endpoint, json_result):
    __mock_api_with_data(monkeypatch, 'post', endpoint, json_result)

def mock_api_get_raw(monkeypatch, endpoint, http_code, json_result):
    __mock_api_raw_without_data(monkeypatch, 'get_raw', endpoint, http_code, json_result)

def mock_api_post_binary(monkeypatch, endpoint, http_code, json_result):
    __mock_api_raw_with_file(monkeypatch, 'post_binary_files_storage', endpoint, http_code, json_result)
```

**Endpoint validation in mocks:** Mocks assert the actual endpoint matches the expected endpoint and raise an `Exception` on mismatch:
```python
def __return_json(actual_endpoint, expected_endpoint, json_result):
    if actual_endpoint == expected_endpoint:
        return json.loads(json_result)
    raise Exception('Fail ! BAD endpoint.\nActual  : %s\nExpected: %s' % (actual_endpoint, expected_endpoint))
```

**Live vs mocked test conditional:** The `monkeypatch` fixture in `conftest.py` returns `None` when running against a real token. All mock helpers guard against this:
```python
def __mock_api_without_data(monkeypatch, method, endpoint, json_result):
    if monkeypatch is not None:  # Skip mock setup when running live
        monkeypatch.setattr(rest_crud, method, ...)
```

**Direct monkeypatch usage for non-REST mocking:**
```python
# tests/commands/test_login.py
monkeypatch.setattr(user_data, 'get_front_url_by_private_entrypoint', lambda: 'http://old-front')

# tests/neoload_cli_lib/test_tools.py
monkeypatch.setattr(os, 'getenv', lambda var, default=None: mock_get_env(mocks, var, default))
```

**What to Mock:**
- All `rest_crud` HTTP methods (get, post, put, patch, delete, get_raw, post_binary_files_storage)
- `user_data.__compute_version_and_path` for login mocking
- `os.getenv` for environment variable tests
- `datetime.datetime` for time-sensitive tests (via `patch_datetime_now` fixture)

**What NOT to Mock:**
- CLI command logic itself — commands are invoked through `CliRunner` which exercises the real code
- File system operations in `tests/resources/` — expected output files are read from disk

## Fixtures and Factories

**conftest.py fixtures:**

```python
# Shared test data as SimpleNamespace
@pytest.fixture
def valid_data():
    return SimpleNamespace(
        test_settings_id='2e4fb86c-ac70-459d-a452-8fa2e9101d16',
        test_result_id='184e0b68-eb4e-4368-9f6e-a56fd9c177cf',
        ...
    )

@pytest.fixture
def invalid_data():
    return SimpleNamespace(uuid='75b63bc2-1234-1234-abcd-f712a69db723')

# Datetime freezing fixture
@pytest.fixture
def patch_datetime_now(monkeypatch):
    class MyDatetime(datetime.datetime):
        @classmethod
        def utcnow(cls): return FAKE_NOW_DATETIME
        @classmethod
        def now(cls, tz=None): return FAKE_NOW_DATETIME
    monkeypatch.setattr(datetime, 'datetime', MyDatetime)
```

**Dynamic name generators** in `tests/helpers/test_utils.py`:
```python
def generate_test_settings_name():
    return 'Test settings CLI %s' % datetime.now(timezone.utc).strftime('%b %d %H:%M:%S.%f')[:-3]
```

**Location:** `tests/resources/` for expected output snapshots and test project files.

## Coverage

**Requirements:** No enforced minimum coverage threshold. SonarCloud scans results but no gates configured in `pytest.ini` or CI that block merges on coverage numbers.

**View Coverage:**
```bash
PYTHONPATH="neoload" coverage run -m pytest
coverage report
coverage html
```

## Test Types

**Unit Tests:**
- Test pure functions in library modules directly
- Located in `tests/neoload_cli_lib/`
- Examples: `test_filtering.py`, `test_tools.py`, `test_user_data.py`
- No CLI invocation; call module functions directly

**Command/Integration Tests:**
- Invoke CLI commands via `click.testing.CliRunner`
- Mock HTTP calls via `monkeypatch` on `rest_crud`
- Located in `tests/commands/`
- Verify output, exit codes, and side effects (status changes)

**Live/Integration Tests:**
- Marked `@pytest.mark.makelivecalls`
- Excluded from default test run via `pytest_configure` in `conftest.py`
- Require `--makelivecalls` flag and real `--token` / `--url`
- Located in `tests/commands/docker/`

**Snapshot/Golden File Tests:**
- `tests/neoload_cli_lib/test_displayer.py` captures stdout and diffs against `tests/resources/expected_*.txt`
- Uses custom `compare_texts()` helper that strips ANSI color codes before comparing

**Acceptance Tests:**
- `tests/test_readme.py` marked `@pytest.mark.acceptance`
- Validates that README examples still work

## Common Patterns

**CLI invocation pattern:**
```python
runner = CliRunner()
result = runner.invoke(settings, ['ls', some_id])
assert_success(result)  # asserts exit_code == 0 and no exception
json_result = json.loads(result.output)
assert json_result['name'] is not None
```

**`assert_success` helper** in `tests/helpers/test_utils.py`:
```python
def assert_success(result):
    if result.exception is not None:
        assert 'EXIT_CODE (%s): %s\n%s' % (result.exit_code, str(result.exception), result.output) == 'no error'
    assert result.exit_code == 0
```

**Error path testing pattern:**
```python
result = runner.invoke(settings, ['ls'])
assert result.exit_code == 1
assert 'You aren\'t logged' in str(result.output)
```

**Exception testing pattern:**
```python
with pytest.raises(click.ClickException) as context:
    user_data.get_user_data()
assert 'You aren\'t logged.' in str(context.value)
```

**Isolated filesystem for file tests:**
```python
with runner.isolated_filesystem():
    with open('bad.json', 'w') as f:
        f.write('{"key": not valid,,,}')
    result = runner.invoke(settings, ['create', '--file', 'bad.json', ...])
```

**Datafiles decorator for file fixtures:**
```python
@pytest.mark.datafiles('tests/neoload_projects/example_1.zip')
@pytest.mark.usefixtures("neoload_login")
def test_upload(self, monkeypatch, datafiles, valid_data):
    zip_path = datafiles / 'example_1.zip'
    ...
```

**Conditional skip for live tests:**
```python
def test_login_nlw_before_2_5_0(self, monkeypatch):
    if monkeypatch is None:
        # Skip this test when using the production environment
        return
```

## pytest Marks Reference

Defined in `pytest.ini`:
- `authentication` — login/logout/status tests
- `settings` — test-settings subcommand tests
- `project` — project subcommand tests
- `results` — test-results subcommand tests
- `validation` — YAML format validation tests
- `acceptance` — README example validation tests
- `workspaces` — workspaces subcommand tests
- `report` — report subcommand tests
- `makelivecalls` — live API tests (excluded by default)
- `fastfail` — fastfail subcommand tests
- `zones` — zones subcommand tests
- `docker` — docker subcommand tests
- `slow` — slow tests (used with `makelivecalls`)

---

*Testing analysis: 2026-04-08*
