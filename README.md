# NeoLoad CLI [![Build Status](https://github.com/Neotys-Labs/neoload-cli/workflows/Python%20package/badge.svg?branch=master)](https://github.com/Neotys-Labs/neoload-cli/actions?query=workflow%3A%22Python+package%22+branch%3A%22master%22)

## Overview

This command-line interface helps you launch and observe performance tests on the Neotys Web Platform. Since NeoLoad is very flexible to many deployment models (SaaS, self-hosted, cloud or local containers, etc.), configuration and test execution parameters depend on your licensing and infrastructure provisioning options.


| Property | Value |
| ----------------    | ----------------   |
| Maturity | Stable |
| Author | Neotys |
| License           | [BSD 2-Clause "Simplified"](https://github.com/Neotys-Labs/neoload-cli/blob/master/LICENSE) |
| NeoLoad Licensing | License FREE edition, or Enterprise edition, or Professional |
| Supported versions | Tested with NeoLoad Web from version [2.3.2](https://neoload.saas.neotys.com)
| Download Binaries | See the [latest release on pypi](https://pypi.org/project/neoload)|

## TL;DR ... What
The goal of this guide is to demonstrate how you can:
 1. create API load tests using code (YAML)
 2. run them from any environment
 3. visualize test results in web dashboards

## TL;DR ... How
```
pip3 install neoload
neoload login $NLW_TOKEN \
        test-settings --zone $NLW_ZONE_DYNAMIC --lgs 5 --scenario sanityScenario createorpatch NewTest1 \
        project --path tests/neoload_projects/example_1 upload NewTest1 \
        run
```
NOTE: For Windows command line, replace the '\\' multi-line separators above with '^'

## Contents

 - [Prerequisites](#prerequisites)
 - [Installation](#installation)
 - [Login to Neoload Web](#login-to-neoload-web)
 - [Setup a test](#setup-a-test)
   - [Setup resources in Neoload Web](#setup-resources-in-neoload-web)
   - [Define a test settings](#define-a-test-settings)
   - [Upload a Neoload project](#upload-a-neoload-project)
     - [Excluding files from the project upload] (#excluding-files-from-the-project-upload)
 - [Run a test](#run-a-test)
   - [Stop a running test](#stop-a-running-test)
 - [Reporting](#reporting)
    - [View results](#view-results)
    - [Exporting Transaction CSV data](#exporting-transaction-CSV-data)
 - [View zones](#view-zones)
 - [Create local docker infrastructure to run a test](#create-local-docker-infrastructure-to-run-a-test)
 - [Continuous Testing Examples](#continuous-testing-examples)
   - [Support for fast-fail based on SLAs](#support-for-fast-fail-based-on-slas)
 - [Packaging the CLI with Build Agents](#packaging-the-cli-with-build-agents)
 - [IDE Integrations](#ide-integrations)
 - [Contributing](#contributing)

## Prerequisites
The CLI requires **Python3**
 - Download and install python3 for **Windows 10** from [Python.org](https://www.python.org/downloads/)
    - Make sure you check the option 'Add Python to the environment variables' option
    - Install pip: ```python -m pip install -U pip```
 - Download and install python3 for **Mac OS X** from [Python.org - Python3 on Mac OS X](https://docs.python-guide.org/starting/install3/osx/)

Optional: Install Docker for hosting the test infra on your machine (this feature does not work with Docker for Windows).

## Installation
```
pip3 install neoload
neoload --help
```

NOTE: if you receive SSL download errors when running the above command, you may also need to install sources using the following command:
```
pip3 install certifi
```

## Login to Neoload Web
NeoLoad CLI defaults to using the NeoLoad Web APIs for most operations. That's why you need to login.
```
neoload login [TOKEN]
neoload login --url http://your-onpremise-neoload-api.com/ --workspace "Default Workspace" your-token
```
The CLI will connect by default to Neoload Web SaaS to lease license. \
For self-hosted enterprise license, you must specify the Neoload Web **Api url** with --url. \
\
The CLI stores data locally like api url, token, the workspace ID and the test ID you are working on. **The commands can be chained !**
```
neoload status          # Displays stored data
```

## Setup a test
### Optionally Choose a workspace to work with
```
Usage: neoload workspaces [OPTIONS] [[ls|use]] [NAME_OR_ID]
neoload workspaces use "Default Workspace"
```
Since Neoload Web 2.5 (August 2020), assets are scoped to workspaces.
The CLI allows you to choose your workspace at login or with the "use" sub-command, otherwise the "Default Workspace" is used.\
**/!\\** The zones are shared between workspaces.


### Setup resources in Neoload Web
Run a test requires an infrastructure that is defined in Neoload Web Zones section [(see documentation how to manage zones)](https://www.neotys.com/documents/doc/nlweb/latest/en/html/#27521.htm#o39458)
You must at least have either a dynamic or a static zone with one controller and one load generator. At First, you could add resources to the "Default zone" since the CLI use it by default.

### Define a test settings
Test settings are how to run a test, a sort of template. Tests are stored in Neoload Web.
```
Usage: neoload test-settings [OPTIONS] [[ls|create|put|patch|delete|use]] [NAME]
neoload test-settings --zone defaultzone --lgs 5 --scenario sanityScenario create NewTest1
```
You must define :
 - Which scenario of the Neoload project to use

You can optionally define :
 - The test-settings description
 - The controller and load generator's zone to use (defaultzone is set by default)
 - How many load generators to use for the zone (1 LG on the defaultzone is set by default)
 - Advanced users who already have several zones with available resources in it, specify all zones and the number of LGs with --controller-zone-id and lg-zone-ids

To work with a specific test already created and be able to chain commands
```
neoload test-settings use NewTest1
neoload test-settings use 4a5e7707-75c0-4106-bbd4-68962ac7f2b3
```

### Upload a Neoload project
See basic projects examples on github [tests/neoload_projects folder](https://github.com/Neotys-Labs/neoload-cli/tree/master/tests/neoload_projects)
To upload a NeoLoad project zip file or a standalone as code file into a test-settings
```
Usage: neoload project [OPTIONS] [up|upload|meta] NAME_OR_ID
neoload project --path tests/neoload_projects/example_1/ upload
```
You must specify in which test the project will be uploaded:
* either by doing this command first
   <pre><code>neoload test-settings use NewTest1</code></pre>
* or by adding the name or id of the test to the project command
   <pre><code>neoload project --path tests/neoload_projects/example_1/ upload NewTest1</code></pre>

To Validate the syntax and schema of the as-code project yaml files
```
neoload validate sample_projects/example_1/default.yaml
```

### Excluding files from the project upload
If you are uploading a project directory that contains non NeoLoad as-code YAML files (such as .gitlab-ci.yml) you will need to create a .nlignore file (exactly the same as .gitignore) that excludes these files from the project upload process so that NeoLoad Web does not parse them and fail them as if they should be the NeoLoad DSL.

Please see Gitlab and Azure pipeline examples for more detail.

## Run a test
This command runs a test, it produces blocking, unbuffered output about test execution process, including readout of current data points.
At the end, displays the summary and the SLA passed & failed.
```
Usage: neoload run [OPTIONS] [NAME_OR_ID]
neoload run \         # Runs the currently used test-settings (see neoload status and neoload test-settings use)
     --as-code default.yaml,slas/uat.yaml \
     --name "MyCustomTestName_${JOB_ID}" \
     --description "A custom test description containing hashtags like #latest or #issueNum"
```
 - detach option kick off a test and returns immediately. Logs are displayed in Neoload Web (follow the url).
 - as-code option specify as-code yaml files to use for the test. They should already be uploaded with the project.
 - Test result name and description can be customized to include CI specific details (e.g. CI job, build number...).
 - Reservations can be used with either the reservationID or a reservation duration and a number of Virtual users.

If you are running in interactive console mode, the NeoLoad CLI will automatically open the system default browser to your live test results. \
When hitting Ctrl+C, the CLI will try to stop the test gracefully

### Stop a running test
```
neoload stop             # Send the stop signal to the test and wait until it ends.
```

## Reporting

There is basic support in the NeoLoad CLI for viewing and exporting results.

### View results
```
Usage: neoload test-results [OPTIONS] [[ls|summary|junitsla|put|delete|use]] [NAME]
neoload test-results ls                 # Lists test results                                            .
neoload test-results use                # Remember the test result you want to work on.                           .
neoload test-results summary            # The Json result summary, with SLAs
neoload test-results junitsla           # Output the summary in a JUnit xml file
```
Metadata on a test can be modified after the test is complete, such as name, description, and status.\

To filter test results based on project, scenario, or status:
```
neoload test-results --filter "project=MyProject;scenario=fullTest" ls
neoload test-results --filter "status=TERMINATED|qualityStatus=FAILED" ls
```
NOTE: you can use either a semicolon OR a pipe, but not both interchangeably in the same filter.

To work with a specific test result and be able to chain commands
```
neoload test-results use 4a5e7707-75c0-4106-bbd4-68962ac7f2b3
```

Detailed logs and results are available on Neoload Web. To get the url of the current result :
```
neoload logs-url                        # The URL to the test in Neoload Web
```

### The test-results vs. report subcommands

The 'test-results' subcommand is intended for direct operational queries against high-level API data.

The 'report' subcommand is intended to simplify not only common data exporting needs, but also provide
 templating capabilities over a standard, correlated data model. In contrast to the test-results
 subcommand, 'report' can be used to generate as well as transform test result data.

### Exporting Transaction CSV data
```
Usage: neoload report [OPTIONS]
neoload report --template builtin:transactions-csv > temp.csv
```

### Filtering export data by timespan
In many load tests, ramp-up and spin-down time is considered irrelevant to calculate into aggregate statistics,
 such as how when warming up, systems may produce higher-than-expected latencies until a steady state is reached.

Therefore, the NeoLoad CLI allows for export of particular time ranges by providing a timespan filter.

```
neoload report --template builtin:transactions-csv --filter "timespan=5m-95%"
neoload report --template builtin:transactions-csv --filter "timespan=15%"
neoload report --template builtin:transactions-csv --filter "timespan=-90%"
```

Timespan format is [Time], then '-' representing to, then another [Time]. Time format can
 be either a human readable duration or percentage of overall test duration.

Human readable time duration format is hour|minute|second such as '1h5m30s' or a sub-portion such as '5m'.

Omitting the end [Time] segment will filter results beginning with the time specified to the end of the test.

Similarly, ommiting the start [Time] segment will filter results beginning with the start of the test
 to the end time specified.

### Filtering export data by element
It is often useful to narrow analysis and statistics to a particular group of activities, such as
 Login processes across multiple workflows (user paths) or other common key business transactions.

Therefore, the NeoLoad CLI allows for exports of specific transcations whose name, parent, or User Path name
 matches specific values or patterns.

```
neoload report --template builtin:transactions-csv --filter "elements=Login"
```
You can filter to specific transactions or requests by specifying 'elements' and then a pipe-delimited list
 of element GUIDs, full names, or partial name matches. This can also include python-compliant regular expressions.

### Combining timespan and element filters
```
neoload report --template builtin:transactions-csv --filter "timespan=50%-95%;elements=AddToCart"
```
Both timespan and elements filters can be combined in order to get statistics for specific elements
 within a precise portion of the test duration. Per the example above, transaction data will be computed
 for elements that have 'AddToCart' somewhere in their name, user path, or parent element and calculate
 aggregates based on data starting from halfway through the test up to just about the very end.

### Exporting All Test Data and Using Custom Templates

If you would like to use multiple templates to create separate output files for specific test data,
 you should dump the test result data using the standard JSON scheme first:
```
neoload report --out-file ~/Downloads/temp.json
```
NOTE: by default, this queries all entity data in test results and may cause multiple API calls
 to occur depending on the structure of the user paths and monitoring data in the test result set.

Then you can produce multiple output files from a single data snapshot:
```
neoload report --json-in ~/Downloads/temp.json \
               --template builtin:transactions-csv \
               --out-file ~/Downloads/temp.csv

neoload report --json-in ~/Downloads/temp.json \
               --template /path/to/a/jinja/template.j2 \
               --out-file ~/Downloads/temp.html
```

NOTE: built-in reports produce a reduced-scope JSON data model and are therefore faster
 that exporting all test data for various templates and output specs.

## View zones
```
neoload zones --human
```
Display in a human-readable way the list of all static and dynamic zones registered on Neoload Web, and the resources attached (controllers and load generators).

## Create local docker infrastructure to run a test [EXPERIMENTAL]

***WARNING: Docker features are not officially supported by Neotys as they rely heavily on your own Docker setup and environment. This command is only for local/dev test scenarios to simplify infrastructure requirements.***

In certain environments, such as on a local dev workstation or in a Docker-in-Docker CI build node, it is useful
 to "bring your own infrastructure". In other words, when you don't already have a controller and load generators
 available in a zone, you can spin some up using Docker before the test starts. An example of an all-on-one approach:

```
neoload docker install

neoload login $NLW_TOKEN \
        test-settings --lgs 2 --scenario sanityScenario create NewTest1 \
        project --path tests/neoload_projects/example_1 upload \
        run
```

What the 'docker install' CLI add step in run command. This step is triggered when zone of controller the test-settings is same than docker.zone (default is defaultzone).
When it is triggered, it launches one controller with number of LG test-settings in docker.zone.
At the end of the run the containers are removed.


The docker container can be launched manually with neoload docker up command and removed with neoload docker down command.
In this case the number of controller and lg is defined by configuration respectively docker.controller.default_count (default: 1) and
docker.lg.default_count (default: 2).


```
Usage: neoload docker [OPTIONS] [up|down|clean|forget|install|uninstall|status]


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

NOTE: Docker CLI must be installed on the system using these commands. This will use
 the Docker daemon, however it is configured. In a Docker-in-Docker context, this is inferred.
 For local workstations, it is sufficient to install Docker Desktop or Docker for Mac.



## Continuous Testing Examples
The main goal of the NeoLoad-CLI is to standardize the semantics of how load tests are executed across development, non-prod, and production environments.
While the above instructions could be run from a contributor workstation, they can easily be translated to various continuous build and deployment orchestration environments, as exampled:

 - [Jenkins](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/jenkins)
 - [Azure DevOps](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/azure_devops)
 - [Gitlab](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/gitlab)
 - [Bamboo](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/bamboo-specs)
 - [AWS](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/aws)
 - CircleCI, TBD when [@punkdata](https://www.linkedin.com/in/punkdata/) gets back to [@paulsbruce](https://www.linkedin.com/in/paulsbruce/) :)

NB: When chaining commands, the return code of the whole command is the return code of the **last command**. That's why you should not chain the two commands "run" and "test-results junitsla".

NOTE: When combining NeoLoad projects and YAML-based pipeline declarations, please see [Excluding files from the project upload] (#excluding-files-from-the-project-upload) to ensure that unecessary artifacts aren't included in the project upload process.

### Support for fast-fail based on SLAs ###

Not all tests succeed. Sometimes environments are down. Sometimes 3rd parties are surprisingly slow. You don't
want to wait for your build pipelines to conduct the whole test duration if it's possible to identify these
issues early. Applying proper SLAs to your tests allows you to monitor for errors and latency during the test.

Consider the following SLA:

```
sla_profiles:
- name: geo_3rdparty_sla
  description: Avg Resp Time >=100ms >= 250ms for cached queries
  thresholds:
  - avg-resp-time warn >= 100ms fail >= 250ms per interval
  - error-rate warn >= 5% fail >= 10% per test
```

If you want to fail the pipeline if either of these thresholds are exceeded over a certain percent of their times,
you must:

- run the test in 'detached' mode to allow for non-blocking execution of a test
- use the fastfail command to monitor for early signals to stop the test if SLAs are violated
- finally wait for the test results

To run the test in detached mode:

```
neoload run \
    --detached
```

Then immediately afterwards, use the fastfail command:
```
neoload fastfail --max-failure 25 slas cur
```

In the above example, '25' represents the percent of times where the SLA was violated, such as 'on a particular
request with an SLA applied, 10 out of 50 times it was executed, the SLA failed'.

Finally, because the test was executed in non-blocking mode, you should wait for the final test result.
```
neoload wait cur
```

[An example for Jenkins pipeline is found here.](examples/pipelines/jenkins/Jenkinsfile_slafails)

## Packaging the CLI with Build Agents
Many of the above CI examples include a step to explicitly install the NeoLoad CLI as part of the
build steps. However, if you want the CLI baked into some build agent directly so that it
is ready for use during a job, here's a Docker example:

For Docker builds [See the test harness Alpine-based Dockerfile](https://github.com/Neotys-Labs/neoload-cli/blob/master/examples/docker/Dockerfile)


## IDE Integrations
Since most of what we do in an IDE is create/edit code, we're mostly interested in how to:
 - make it easy to write API tests in YAML (automatic syntax validation)
 - validate that tests do not contain unanticipated errors even at small scale
 - dry-run small (smoke) load tests locally so that code check-ins will work in CI/pipeline tests

Since the latter two cases are already covered by command-line semantics, our primary focus
is to accelerate test authoring by providing NeoLoad as-code DSL (Domain-specific Language) validation
and in some cases editor auto-complete.

Status of IDE / editor integrations

 | IDE / Editor       | Syntax checks | Auto-complete | Setup steps
 |:------------------:|:-------------:|:-------------:|:----------------:|
 | Visual Studio Code |      [x]      |      [x]      | [see instructions](resources/ides/vscode_settings.json) |
 | PyCharm |      [x]      |      [x]      | Mark 'neoload' directory as "Sources Root" |

## Contributing
Feel free to fork this repo, make changes, *test locally*, and create a pull request.

### Local Verification

#### Tests
As part of your testing, you should run the built-in test suite with the following command: \
NOTE: for testing from Mac, please change the PYTHONPATH separators below to colons (:) instead of semicolons (;).

```
PYTHONPATH="neoload;tests/helpers" pytest -v
PYTHONPATH="neoload;tests/helpers" pytest -v -m "not slow"          # Skip slow tests that run tests

# Run on a real Neoload. Mocks are disabled
PYTHONPATH="neoload;tests/helpers" pytest -v --token <your_personal_token> --url https://neoload-api.saas.neotys.com/
```

Additionally, any contributions to the DSL validation functionality, such as on the JSON schema or the validate command, should execute the following tests locally before pushing to this repo:
```
./tests/neoload_projects/yaml_variants/validate_all.sh
```
This command executes a number of NEGATIVE tests to prove that changes to the JSON schema or validation process produce failures when their input is malformed in very specific ways (common mistakes).

### Release Process (managed by Neotys team)

#### Auto-generating Changelog

Before tagging a release, merged PRs should update the CHANGELOG.md via the following:

```
github_changelog_generator -u Neotys-Labs -p neoload-cli --token $GIT_CHANGELOG_GEN --exclude-tags-regex ".*(dev|rc).*" --add-sections '{"documentation":{"prefix":"**Documentation updates:**","labels":["documentation"]}}'
```

This utility is a [Ruby-based GEM](https://github.com/github-changelog-generator/github-changelog-generator) that can be installed (also used in CI/Actions) as follows:

```
gem install github_changelog_generator
```

#### Version management on pypi
Suppose X, Y, Z and N are integers, versions will be named as following on pypi: \
**Final release version = X.Y.Z** Example *1.4.0* Install it with ```pip install neoload``` \
**Release candidate version = X.Y.ZrcN** Example *1.5.0rc1* for the next candidate version. Install it with ```pip install neoload --pre``` \
**Development versions = X.Y.Z.devN** Example *1.4.0.dev1* for a development version based on the final release 1.4.0. Install it with ```pip install neoload==1.4.0.dev1```

Release candidate version contains all features planned and in testing by Quality Assurance team.

Development versions may contains work not planned by R&D and not tested by Quality Assurance team. They should always be based on an official release, not on the next release.

**Increment policy:**
 - Minor version increment when major feature, for example new top-level command
 - Fix version increment when executable changes, for example fixing an existing feature, or update a subcommand to an existing top-level command or update options to an existing command
 - No release needed when the executable is not modified, for example when updating the following: automated CI tests, unit tests, README, Pipeline examples, report templates...
