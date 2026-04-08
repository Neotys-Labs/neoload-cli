# Technology Stack

**Analysis Date:** 2026-04-08

## Languages

**Primary:**
- Python 3 - All CLI source code in `neoload/` and `tests/`

**Secondary:**
- Jinja2 templates (`.j2`) - Report generation in `neoload/resources/jinja/`
- YAML - Project configuration, test definitions, internal config storage

## Runtime

**Environment:**
- Python 3.8+ (CI matrix tests against 3.8 and 3.11; `.travis.yml` tested 3.6 and 3.8)

**Package Manager:**
- pip
- Lockfile: Not present (no `requirements.lock` or `Pipfile.lock`); `requirements.txt` lists only test deps

## Frameworks

**Core:**
- `click>=7` - CLI framework, command routing, option/argument parsing (`neoload/__main__.py`, all `neoload/commands/*.py`)

**Testing:**
- `pytest` - Test runner (`pytest.ini`, `tests/`)
- `pytest-datafiles` - Fixture-based file loading for tests
- `pytest-mock` - Monkeypatching/mock support
- `coverage` - Code coverage (used in CI, produces `coverage.xml`)

**Build/Dev:**
- `setuptools_scm==9.2.2` - Version management from git tags (`setup.py`)
- `setuptools`, `wheel`, `twine` - Package build and publish (used in CI release workflow)

## Key Dependencies

**Critical:**
- `click>=7` - Entire CLI framework; all commands are click-decorated functions
- `requests>=2.25.1` - All HTTP communication with NeoLoad Web API (`neoload/neoload_cli_lib/rest_crud.py`)
- `requests_toolbelt` - Multipart file upload with progress monitoring (`rest_crud.py`)
- `docker` - Docker SDK for Python; manages NeoLoad controller/loadgenerator containers (`neoload/neoload_cli_lib/docker_lib.py`)
- `jinja2` - Report template rendering (`neoload/commands/report.py`, templates in `neoload/resources/jinja/`)
- `PyYAML>=5` - YAML config file read/write for user data and global config (`neoload/neoload_cli_lib/user_data.py`, `config_global.py`)
- `jsonschema` - Draft7 JSON schema validation of NeoLoad YAML project files (`neoload/neoload_cli_lib/schema_validation.py`)

**Infrastructure:**
- `appdirs` - Platform-appropriate user data directory resolution (`neoload/neoload_cli_lib/user_data.py`, `paths.py`)
- `urllib3>=1.26.5` - HTTP library (warnings suppressed in `__main__.py`); retry logic in `rest_crud.py`
- `tqdm` - Progress bar for file uploads (`rest_crud.py`)
- `coloredlogs` - Colored log output in terminal (`__main__.py`)
- `termcolor` - Colored print output (`neoload/neoload_cli_lib/tools.py`)
- `colorama` - Cross-platform terminal color support
- `junit_xml` - JUnit XML SLA report output (`neoload/commands/test_results.py`)
- `python-dateutil` - Date parsing for Python 3.6 compatibility (`neoload/commands/report.py`)
- `simplejson` - JSON parsing with `JSONDecodeError` import (`neoload/neoload_cli_lib/user_data.py`)
- `gitignorefile` - `.nlignore` file parsing to exclude files during project upload (`neoload/neoload_cli_lib/neoLoad_project.py`, `schema_validation.py`)
- `pyparsing` - Parsing utilities
- `pyconfig` - Configuration support
- `importlib-resources` - Resource file access for packaged Jinja templates

## Configuration

**Environment:**
- No `.env` file; credentials passed via CLI options (`neoload login <token> --url <url>`)
- Config stored at `appdirs.user_data_dir("neoload-cli", "neotys", "1.0")/config.yaml` or `.neoload_cli.yaml` in current dir
- Global CLI config at `appdirs.user_data_dir(...)/config-global.yaml` (`neoload/neoload_cli_lib/config_global.py`)
- YAML schema cached at `appdirs.user_data_dir(...)/yaml_schema.json`
- CI environment auto-detected via env vars (Jenkins, Travis, Bamboo, CodeBuild, Azure, GitLab, TeamCity, CircleCI, GCB) in `neoload/neoload_cli_lib/tools.py`

**Build:**
- `setup.py` - Package definition; version managed via `setuptools_scm` from git tags
- `MANIFEST.in` - Controls which non-Python files are packaged

## Platform Requirements

**Development:**
- Python 3.8+
- Docker daemon (optional, for `neoload docker` commands)
- Internet access (for NeoLoad Web API and schema downloads from GitHub raw content)

**Production:**
- Installed via `pip install neoload`
- Distributed on PyPI as the `neoload` package
- Entry point: `neoload` CLI command mapped to `neoload.__main__:cli`

---

*Stack analysis: 2026-04-08*
