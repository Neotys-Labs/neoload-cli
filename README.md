# NeoLoad CLI [![Build Status](https://travis-ci.org/Neotys-Labs/neoload-cli.svg?branch=master)](https://travis-ci.org/Neotys-Labs/neoload-cli)

## Overview

This command-line interface helps you launch and observe performance tests on the Neotys Web Platform. Since NeoLoad is very flexible to many deployment models (SaaS, self-hosted, cloud or local containers, etc.), configuration and test execution parameters depend on your licensing and infrastructure provisioning options.


| Property | Value |
| ----------------    | ----------------   |
| Maturity | Experimental |
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
        test-settings --zone $NLW_ZONE_DYNAMIC --lgs 5 --scenario sanityScenario create NewTest1 \
        project --path tests/neoload_projects/example_1 upload \
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
 - [Run a test](#run-a-test)
   - [Stop a running test](#stop-a-running-test)
 - [View results](#view-results)
 - [View zones](#view-zones)
 - [Create local docker infrastructure to run a test](#create-local-docker-infrastructure-to-run-a-test)
 - [Continuous Testing Examples](#continuous-testing-examples)
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

## Login to Neoload Web
NeoLoad CLI defaults to using the NeoLoad Web APIs for most operations. That's why you need to login.
```
neoload login [TOKEN]
neoload login --url http://your-onpremise-neoload-api.com/ your-token
```
The CLI will connect by default to Neoload Web SaaS to lease license. \
For self-hosted enterprise license, you must specify the Neoload Web Api url with --url. \
\
The CLI stores data locally like api url, token, and the test ID you are working on. **The commands can be chained !**
```
neoload status          # Displays stored data
```

## Setup a test
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
To Validate the syntax and schema of the as-code project yaml files
```
neoload validate sample_projects/example_1/default.yaml
```

## Run a test
This command runs a test, it produces blocking, unbuffered output about test execution process, including readout of current data points.
At the end, displays the summary and the SLA passed & failed.
```
Usage: neoload run [OPTIONS] [NAME_OR_ID]
neoload run \         # Runs the currently used test-settings (see neoload status)
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

## View results
```
Usage: neoload test-results [OPTIONS] [[ls|summary|junitsla|put|delete|use]] [NAME]
neoload test-results summary            # The Json result summary, with SLAs
neoload test-results junitsla           # Output the summary in a JUnit xml file
```
Metadata on a test can be modified after the test is complete, such as name, description, and status.\

To work with a specific test result and be able to chain commands
```
neoload test-results use 4a5e7707-75c0-4106-bbd4-68962ac7f2b3
```

Detailed logs and results are available on Neoload Web. To get the url of the current result :
```
neoload logs-url                        # The URL to the test in Neoload Web
```

## View zones
```
neoload zones --human
```
Display in a human readable way the list of all static and dynamic zones registered on Neoload Web, and the resources attached (controllers and load generators).

## Create local docker infrastructure to run a test
Upcoming

## Continuous Testing Examples
The main goal of the NeoLoad-CLI is to standardize the semantics of how load tests are executed across development, non-prod, and production environments.
While the above instructions could be run from a contributor workstation, they can easily be translated to various continuous build and deployment orchestration environments, as exampled:

 - [Jenkins](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/jenkins_pipeline)
 - [Azure DevOps](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/azure_devops)
 - [Gitlab](https://github.com/Neotys-Labs/neoload-cli/tree/master/examples/pipelines/gitlab)
 - Sorry AWS CodeBuild, haven't seen any F100 clients using the pform
 - CircleCI, TBD when [@punkdata](https://www.linkedin.com/in/punkdata/) gets back to [@paulsbruce](https://www.linkedin.com/in/paulsbruce/) :)

NB: When chaining commands, the return code of the whole command is the return code of the **last command**. That's why you should not chain the two commands "run" and "test-results junitsla".

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
Feel free to fork this repo, make changes, *test locally*, and create a pull request. As part of your testing, you should run the built-in test suite with the following command:
```
PYTHONPATH="neoload;tests/helpers" pytest -v
PYTHONPATH="neoload;tests/helpers" pytest -v -m "not slow"          # Skip slow tests that run tests

# Run on a real Neoload. Mocks are disabled
PYTHONPATH="neoload;tests/helpers" pytest -v --token <your_personal_token> --url https://neoload-api.saas.neotys.com/
```
