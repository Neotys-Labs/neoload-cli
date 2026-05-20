# NeoLoad CLI [![Python package](https://github.com/Neotys-Labs/neoload-cli/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/Neotys-Labs/neoload-cli/actions/workflows/python-package.yml)

## Overview

This command-line interface lets you launch and monitor performance tests on the NeoLoad Web platform. Because NeoLoad supports many deployment models (SaaS, self-hosted, cloud or local containers, etc.), the configuration and test execution parameters depend on your licensing and infrastructure setup.


| Property | Value |
| ----------------    | ----------------   |
| Maturity | Stable |
| Author | Tricentis |
| License           | [BSD 2-Clause "Simplified"](https://github.com/Neotys-Labs/neoload-cli/blob/master/LICENSE) |
| NeoLoad Licensing | FREE, Professional, or Enterprise edition |
| Supported versions | Tested with NeoLoad Web from version [2.3.2](https://neoload.saas.neotys.com) |
| Download Binaries | See the [latest release on PyPI](https://pypi.org/project/neoload) |

## TL;DR ... What
This guide shows you how to:
 1. create API load tests as code (YAML)
 2. run them from any environment
 3. visualize the test results in web dashboards

## TL;DR ... How
```
pip3 install neoload
neoload login $NLW_TOKEN \
        test-settings --zone $NLW_ZONE_DYNAMIC --lgs 5 --scenario sanityScenario createorpatch NewTest1 \
        project --path tests/neoload_projects/example_1 upload NewTest1 \
        run
```
NOTE: On the Windows command line, replace the `\` line-continuation characters above with `^`.

## Contents

 - [Prerequisites](#prerequisites)
 - [Installation](#installation)
 - [Login to NeoLoad Web](#login-to-neoload-web)
 - [Setup a test](#setup-a-test)
   - [Setup resources in NeoLoad Web](#setup-resources-in-neoload-web)
   - [Define a test](#define-a-test)
   - [Upload a NeoLoad project](#upload-a-neoload-project)
     - [Excluding files from the project upload](#excluding-files-from-the-project-upload)
 - [Run a test](#run-a-test)
   - [Stop a running test](#stop-a-running-test)
 - [Reporting](#reporting)
    - [View results](#view-results)
    - [Exporting Transaction CSV data](#exporting-transaction-csv-data)
 - [View zones](#view-zones)
 - [Create local Docker infrastructure to run a test](#create-local-docker-infrastructure-to-run-a-test)
 - [Continuous Testing Examples](#continuous-testing-examples)
   - [Support for fast-fail based on SLAs](#support-for-fast-fail-based-on-slas)
 - [Packaging the CLI with Build Agents](#packaging-the-cli-with-build-agents)
 - [IDE Integrations](#ide-integrations)
 - [Contributing](#contributing)

## Prerequisites
The CLI requires **Python 3**.
 - Download and install Python 3 for **Windows** from [Python.org](https://www.python.org/downloads/).
    - Make sure you check the option *Add Python to the environment variables*.
    - Install pip: ```python -m pip install -U pip```
 - Download and install Python 3 for **macOS** from [Python.org - Python 3 on macOS](https://docs.python-guide.org/starting/install3/osx/).

Optional: install Docker if you want to host the test infrastructure on your machine (this feature is not supported with Docker for Windows).

## Installation
```
pip3 install neoload
neoload --help
```

NOTE: if you receive SSL download errors when running the command above, you may also need to install the trusted root certificates with:
```
pip3 install certifi
```

## Login to NeoLoad Web
The NeoLoad CLI uses the NeoLoad Web APIs for most operations, so you must log in before running any commands.
```
neoload login [TOKEN]
neoload login --url http://your-onpremise-neoload-api.com/ --workspace "Default Workspace" your-token
```
By default, the CLI connects to NeoLoad Web SaaS to lease a license. \
For a self-hosted Enterprise license, you must specify the NeoLoad Web **API URL** with `--url`.

The CLI stores data locally, such as the API URL, token, workspace ID, and the test ID you are currently working on. **Commands can be chained!**
```
neoload status          # Displays stored data
```

## Setup a test
### Optionally choose a workspace to work with
```
Usage: neoload workspaces [OPTIONS] [[ls|use]] [NAME_OR_ID]
Help: neoload workspaces --help
neoload workspaces use "Default Workspace"
```
You can select your workspace at login or with the `use` sub-command. If no workspace is specified, the "Default Workspace" is used. \
**/!\\** Zones are shared between workspaces.


### Setup resources in NeoLoad Web
Running a test requires an infrastructure defined in the NeoLoad Web *Zones* section ([see the documentation on how to manage zones](https://documentation.tricentis.com/nlweb/latest/en/content/reference_guide/resources_zones.htm)).
At a minimum, you need either a dynamic or a static zone containing one controller and one load generator. The simplest approach is to add resources to the "Default zone", since the CLI uses it by default.

### Define a test
A NeoLoad Web test contains the test configuration and the list of its test results. You can analyze transaction values across the most recent test results to detect regressions.
```
Usage: neoload test-settings [OPTIONS] [[ls|create|put|patch|delete|use|createorpatch]] [NAME]
Help: neoload test-settings --help
neoload test-settings --zone defaultzone --lgs 5 --scenario sanityScenario create NewTest1
```
You can optionally define:
 - which scenario of the NeoLoad project to use
 - the test-settings description
 - the controller and load generator zone to use (defaults to `defaultzone`)
 - how many load generators to use in the zone (defaults to 1 LG on `defaultzone`)
 - advanced users with multiple zones that have available resources can use: ```--zone my_controller_zone --lgs lg_zoneA:2,lg_zoneB:3```

To work with an existing test and chain commands against it:
```
neoload test-settings use NewTest1
neoload test-settings use 4a5e7707-75c0-4106-bbd4-68962ac7f2b3
```

### Upload a NeoLoad project
For basic project examples, see the [`tests/neoload_projects` folder on GitHub](https://github.com/Neotys-Labs/neoload-cli/tree/master/tests/neoload_projects).

To upload a NeoLoad project (a ZIP file, a folder or a standalone as-code file) into a test-settings:
```
Usage: neoload project [OPTIONS] [up|upload|meta] NAME_OR_ID
Help: neoload project --help
neoload project --path tests/neoload_projects/example_1/ upload
```
You must indicate which test the project should be uploaded to, either by:
* running this command first:
   <pre><code>neoload test-settings use NewTest1</code></pre>
* or by appending the name or ID of the test to the `project` command:
   <pre><code>neoload project --path tests/neoload_projects/example_1/ upload NewTest1</code></pre>
:warning: If the test has no scenario, or if the configured scenario does not exist in the project, the "Custom" scenario is selected by default (10 VUs for 5 minutes).

To validate the syntax and schema of the as-code project YAML files:
```
neoload validate sample_projects/example_1/default.yaml
```

### Excluding files from the project upload
If you upload a project directory that contains YAML files which are not NeoLoad as-code (such as `.gitlab-ci.yml`), you must create a `.nlignore` file (using the same syntax as `.gitignore`) to exclude those files from the upload. Otherwise, NeoLoad Web will try to parse them as NeoLoad as-code files and fail.

For details, see the GitLab and Azure pipeline examples.

## Run a test
This command runs a test. It produces blocking, unbuffered output describing the execution progress, including current data points.
When the test completes, it displays a summary along with the SLAs that passed and failed.
```
Usage: neoload run [OPTIONS] [NAME_OR_ID]
Help: neoload run --help
neoload run \         # Runs the currently selected test-settings (see neoload status and neoload test-settings use)
     --as-code default.yaml,slas/uat.yaml \
     --scenario scenario1
     --name "MyCustomTestName_${JOB_ID}" \
     --description "A custom test description containing hashtags like #latest or #issueNum"
```
 - `--detached` starts the test and returns immediately. Logs are available in NeoLoad Web (follow the URL).
 - `--as-code` specifies the as-code YAML files to use for the test. They must already be uploaded with the project.
 - `--scenario` specifies the name of the scenario to run. The scenario must be declared either in an as-code YAML file or in the project; otherwise the NeoLoad Web "Custom" scenario is used (10 VUs for 5 minutes).
 - The test result name and description can be customized to include CI-specific details (e.g. CI job, build number, etc.).
 - Reservations can be used with either a reservation ID, or a reservation duration combined with a number of virtual users.

When running in interactive console mode, the NeoLoad CLI automatically opens your system's default browser to display the live test results. \
Pressing `Ctrl+C` causes the CLI to attempt to stop the test gracefully.

### Stop a running test
```
neoload stop             # Sends the stop signal to the test and waits until it ends.
```

## Reporting

The NeoLoad CLI provides basic support for viewing and exporting test results.

### View results
```
Usage: neoload test-results [OPTIONS] [[ls|summary|junitsla|put|patch|delete|use]] [NAME]
Help: neoload test-results --help
neoload test-results ls                 # Lists test results
neoload test-results use                # Remembers the test result you want to work on.
neoload test-results summary            # JSON result summary, including SLAs
neoload test-results junitsla           # Outputs the summary as a JUnit XML file
```
Test metadata such as name, description, and status can be modified after the test is complete.

To filter test results by project, scenario, or status:
```
neoload test-results --filter "project=MyProject;scenario=fullTest" ls
neoload test-results --filter "status=TERMINATED|qualityStatus=FAILED" ls
```
NOTE: you can use either a semicolon or a pipe as the separator, but not both in the same filter.

To select a specific test result so that subsequent commands can be chained against it:
```
neoload test-results use 4a5e7707-75c0-4106-bbd4-68962ac7f2b3
```

Detailed logs and results are available on NeoLoad Web. To get the URL of the current result:
```
neoload logs-url                        # The URL of the test in NeoLoad Web
```

### The test-results vs. report subcommands

The `test-results` subcommand is intended for direct operational queries against high-level API data.

The `report` subcommand is intended to simplify common data exporting needs and to provide templating capabilities over a standard, correlated data model. Unlike `test-results`, the `report` subcommand can be used to both generate and transform test result data.

:warning: The `report` subcommand can be **slow** (up to several hours) on results that contain many transactions or monitors.

### Exporting Transaction CSV data
```
Usage: neoload report [OPTIONS] [NAME]
Help: neoload report --help
neoload report --template builtin:transactions-csv "test_result_name_or_id" > temp.csv
```

### Filtering export data by timespan
In many load tests, the ramp-up and spin-down periods are not relevant to aggregate statistics. For example, while a system is warming up, it may produce higher-than-expected latencies until a steady state is reached.

The NeoLoad CLI therefore lets you export specific time ranges by providing a timespan filter.

```
neoload report --template builtin:transactions-csv --filter "timespan=5m-95%"
neoload report --template builtin:transactions-csv --filter "timespan=15%"
neoload report --template builtin:transactions-csv --filter "timespan=-90%"
```

The timespan format is `[Time]-[Time]`, where each `[Time]` is either a human-readable duration or a percentage of the total test duration.

The human-readable duration format combines hours, minutes, and seconds, for example `1h5m30s` or just `5m`.

Omitting the end `[Time]` filters the results from the specified time to the end of the test.

Similarly, omitting the start `[Time]` filters the results from the beginning of the test to the specified end time.

### Filtering export data by element
It is often useful to narrow analysis and statistics down to a specific group of activities, such as login processes across multiple workflows (user paths) or other key business transactions.

The NeoLoad CLI therefore lets you export specific transactions whose name, parent, or user path name matches a given value or pattern.

```
neoload report --template builtin:transactions-csv --filter "elements=Login"
```
You can filter to specific transactions or requests by passing `elements` followed by a pipe-delimited list of element GUIDs, full names, or partial name matches. The values can also be Python-compatible regular expressions.

### Combining timespan and element filters
```
neoload report --template builtin:transactions-csv --filter "timespan=50%-95%;elements=AddToCart"
```
The timespan and elements filters can be combined to compute statistics for specific elements within a precise portion of the test. In the example above, the report includes elements that contain `AddToCart` in their name, user path, or parent element, and the aggregates are calculated from halfway through the test to almost the very end.

### Exporting all test data and using custom templates

If you want to use multiple templates to create separate output files for the same test data, dump the test result data first using the standard JSON schema:
```
neoload report --out-file ~/Downloads/temp.json
```
NOTE: by default, this queries all entity data for the test results and will trigger multiple API calls, depending on the structure of the user paths and monitoring data in the test result set.

You can then produce multiple output files from a single data snapshot:
```
neoload report --json-in ~/Downloads/temp.json \
               --template builtin:transactions-csv \
               --out-file ~/Downloads/temp.csv

neoload report --json-in ~/Downloads/temp.json \
               --template /path/to/a/jinja/template.j2 \
               --out-file ~/Downloads/temp.html
```

NOTE: built-in reports produce a reduced-scope JSON data model and are therefore faster than exporting all test data for various templates and output formats.

### Working with large result sets

In the context of the CLI, a "large result set" means several hundred transactions, with several load generators, running for several hours.

The `report` subcommand retrieves a large amount of data from the NeoLoad Web API and is not recommended for large result sets, as it may take several hours to complete and can fail.

The `report` subcommand fetches all the `values` and `timeseries points` for every statistic from the NeoLoad Web API, for each transaction and monitor. \
It makes 2 API calls per transaction and 1 API call per monitor. Up to 10 calls run in parallel (configurable via the `NL_MAX_WORKERS` environment variable). \
On NeoLoad Web SaaS, the rate limit of 300 calls per minute may be reached, in which case the CLI will adapt and slow down accordingly.

To see which NeoLoad Web API calls are made, set the CLI log level to debug: `neoload --debug report`.

## View zones
```
neoload zones --human
Help: neoload zones --help
```
Displays a human-readable list of all static and dynamic zones registered in NeoLoad Web, along with the resources attached to each (controllers and load generators).

## Create local Docker infrastructure to run a test [EXPERIMENTAL]

***WARNING: Docker features are not officially supported by Tricentis as they rely heavily on your local Docker setup and environment. This command is intended only for local/dev test scenarios, to simplify infrastructure requirements.***

In certain environments, such as a local development workstation or a Docker-in-Docker CI build node, it is useful to "bring your own infrastructure". In other words, when no controller and load generators are already available in a zone, you can spin them up with Docker before the test starts. Here is an all-in-one example:

```
neoload docker install

neoload login $NLW_TOKEN \
        test-settings --lgs 2 --scenario sanityScenario create NewTest1 \
        project --path tests/neoload_projects/example_1 upload \
        run
```

`docker install` adds an extra step to the `run` command. This step is triggered when the controller zone defined in the test-settings matches `docker.zone` (default: `defaultzone`).
When triggered, it launches one controller along with the number of load generators specified in the test-settings, inside `docker.zone`.
The containers are removed at the end of the test.


You can also launch the Docker containers manually with `neoload docker up` and remove them with `neoload docker down`.
In this case, the number of controllers and load generators is taken from `docker.controller.default_count` (default: 1) and `docker.lg.default_count` (default: 2) respectively.


```
Usage: neoload docker [OPTIONS] [up|down|clean|forget|install|uninstall|status]
Help: neoload docker --help


neoload docker up / down         # start or delete container depend on configuration
neoload docker install/uninstall # add/remove hooks on run command to up when the controller zone is same and zone is empty. Shut down at the end of test running.
neoload docker forget            # remove container from the launched list. That avoid to be removed with down command.
neoload docker clean             # remove all container created by neoload-cli even if it was forgotten.
neoload docker status            # display configuration and general status.

Options:
  --no-wait  Do not wait for controller and load generator in zones api
  --help     Show this message and exit.

Configuration:
  - docker.controller.image (default:  neotys/neoload-controller:latest)
  - docker.controller.default_count (default: 1)
  - docker.lg.image (default: neotys/neoload-loadgenerator:latest)
  - docker.lg.default_count (default: 2)
  - docker.zone (default: defaultzone)

```

NOTE: the Docker CLI must be installed on the system for these commands to work. The CLI relies on whatever Docker daemon is configured. In a Docker-in-Docker context, this is detected automatically. On local workstations, installing Docker Desktop or Docker for Mac is sufficient.


## CLI configuration
```
neoload config ls
neoload config set docker.lg.default_count=1
Help: neoload config --help
```
The configuration lets you customize the CLI's behavior. For now, it is only used by the `docker` command (see above).

## Continuous Testing Examples
The main goal of the NeoLoad CLI is to standardize how load tests are executed across development, non-prod, and production environments.
The instructions above can be run from a contributor workstation, but they can also be easily translated to various continuous build and deployment platforms. Examples are provided for:

 - [Jenkins](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/jenkins)
 - [GitHub](https://github.com/Neotys-Labs/neoload-cli/blob/master/examples/pipelines/github/neoload-github-actions-demo.yml)
 - [Azure DevOps](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/azure_devops)
 - [GitLab](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/gitlab)
 - [AWS](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/aws)
 - [Bamboo](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/bamboo-specs)


NB: when chaining commands, the return code of the whole chain is the return code of the **last command**. For that reason, you should not chain `run` with `test-results junitsla`.

NOTE: when combining NeoLoad projects with YAML-based pipeline declarations, see [Excluding files from the project upload](#excluding-files-from-the-project-upload) to make sure unnecessary artifacts are not included in the upload.

### Support for fast-fail based on SLAs ###

Not every test succeeds. Sometimes environments are down, sometimes third-party services are unexpectedly slow. When such issues can be detected early, you don't want your build pipeline to wait for the full test duration to fail. Applying proper SLAs to your tests lets you monitor errors and latency while the test is running.

Consider the following SLA:

```
sla_profiles:
- name: geo_3rdparty_sla
  description: Avg Resp Time >=100ms >= 250ms for cached queries
  thresholds:
  - avg-resp-time warn >= 100ms fail >= 250ms per interval
  - error-rate warn >= 5% fail >= 10% per test
```

To fail the pipeline as soon as either of these thresholds is exceeded beyond a given percentage of the time, you need to:

- run the test in `--detached` mode so the test runs asynchronously
- use the `fastfail` command to monitor for early SLA violations and stop the test if needed
- finally, wait for the test results

Run the test in detached mode:

```
neoload run \
    --detached
```

Then, immediately afterwards, run the `fastfail` command:
```
neoload fastfail --max-failure 25 slas cur
```

In this example, `25` represents the percentage of evaluations in which the SLA was violated. For instance, if an SLA-protected request was executed 50 times and the SLA failed 10 of those times, that is a 20% failure rate.

Finally, because the test was started in non-blocking mode, you must wait for the final test result:
```
neoload wait cur
```

[See here for a Jenkins pipeline example.](examples/pipelines/jenkins/Jenkinsfile_slafails)

## Troubleshooting
### Set debug log level
Use `neoload --debug ...` to show verbose logs from the neoload-cli.

### Windows and non-UTF-8 characters
Windows uses ASCII as the default encoding, but the NeoLoad CLI requires UTF-8. \
Before running commands such as `neoload report` on Windows, you need to set the environment variable `set PYTHONUTF8=1`. \
For more information, see [the Windows UTF-8 mode docs](https://docs.python.org/3/using/windows.html#utf-8-mode) and [the os module docs](https://docs.python.org/3/library/os.html#utf8-mode).
Starting with Python 3.15, this is no longer necessary; see [PEP 686 – Make UTF-8 mode default](https://peps.python.org/pep-0686/).


## Packaging the CLI with Build Agents
Many of the CI examples above install the NeoLoad CLI as one of the build steps. If you would rather bake the CLI directly into a build agent so it is ready to use during a job, see the following Docker example:

For Docker builds, [see the test harness Alpine-based Dockerfile](https://github.com/Neotys-Labs/neoload-cli/blob/master/examples/docker/Dockerfile).


## IDE Integrations
Most of the work done in an IDE is creating and editing code, so we are mainly interested in being able to:
 - easily write API tests in YAML (with automatic syntax validation)
 - validate that tests do not contain unexpected errors, even at small scale
 - run small (smoke) load tests locally so that code check-ins will work in CI/pipeline tests

The last two cases are already covered by the CLI itself, so our primary focus for IDE integrations is to accelerate test authoring by providing validation for the NeoLoad as-code DSL (Domain-Specific Language), and, in some cases, editor auto-complete.

Status of IDE / editor integrations:

 | IDE / Editor       | Syntax checks | Auto-complete | Setup steps
 |:------------------:|:-------------:|:-------------:|:----------------:|
 | Visual Studio Code |      [x]      |      [x]      | [See instructions](resources/ides/vscode_settings.json) |
 | PyCharm            |      [x]      |      [x]      | Mark the `neoload` directory as "Sources Root" |

## Contributing
Feel free to fork this repo, make your changes, *test locally*, and then open a pull request.

### Local verification

#### Tests
As part of your testing, run the built-in test suite with the following commands. \
NOTE: when testing on macOS, replace the semicolons (`;`) in `PYTHONPATH` with colons (`:`).

```
pytest -v
pytest -v -m "not slow"          # Skip slow tests

# Run against a real NeoLoad instance. Mocks are disabled.
pytest -v --token <your_personal_token> --url https://neoload-api.saas.neotys.com/ --makelivecalls

# Run the integration tests. These execute scripts using real neoload commands and assert the JSON output with jq.
# Requires at least 1 controller and 1 LG on the provided zone.
./tests/integration/runAllScripts.sh <your_personal_token> --url https://neoload-api.saas.neotys.com/ defaultzone
```

In addition, any contribution to the DSL validation functionality (for example, to the JSON schema or the `validate` command) should run the following tests locally before pushing:
```
./tests/neoload_projects/yaml_variants/validate_all.sh
```
This command runs a series of NEGATIVE tests that ensure changes to the JSON schema or validation process correctly produce failures when the input is malformed in specific, common ways.

### Release process (managed by the Tricentis NeoLoad team)

#### Auto-generating the changelog

Before tagging a release, merged PRs should update `CHANGELOG.md` using the following command:

```
github_changelog_generator -u Neotys-Labs -p neoload-cli --token $GIT_CHANGELOG_GEN --exclude-tags-regex ".*(dev|rc).*" --add-sections '{"documentation":{"prefix":"**Documentation updates:**","labels":["documentation"]}}'
```

This utility is a [Ruby-based gem](https://github.com/github-changelog-generator/github-changelog-generator) (also used in CI/Actions) that can be installed with:

```
gem install github_changelog_generator
```

#### Version management on PyPI
Given that X, Y, Z, and N are integers, versions on PyPI are named as follows: \
**Final release version = X.Y.Z** — example: *1.4.0*. Install it with ```pip install neoload``` \
**Release candidate version = X.Y.ZrcN** — example: *1.5.0rc1* for the next candidate version. Install it with ```pip install neoload --pre``` \
**Development version = X.Y.Z.devN** — example: *1.4.0.dev1* for a development version based on the final release 1.4.0. Install it with ```pip install neoload==1.4.0.dev1```

A release candidate version contains all the features planned for the release and is undergoing testing by the Quality Assurance team.

Development versions may contain work that is not planned by R&D and has not been tested by the Quality Assurance team. They should always be based on an official release, not on an upcoming one.

**Increment policy:**
 - Increment the minor version for a major feature, such as a new top-level command.
 - Increment the patch version for executable changes, such as fixing an existing feature, updating a subcommand of an existing top-level command, or updating the options of an existing command.
 - No release is needed when the executable is not modified, for example when only updating automated CI tests, unit tests, the README, pipeline examples, or report templates.
