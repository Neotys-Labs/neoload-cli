# NeoLoad CLI

This command-line interface helps you launch and observe performance tests on the Neotys Platform. Since NeoLoad is very flexible to many deployment models (SaaS, self-hosted, cloud or local containers, etc.), configuration and test execution parameters depend on your licensing and infrastructure provisioning options. Please read the following instructions carefully.

## Prerequisites
The examples below assume that you have Python3 and Git command line tools installed.

For Windows users, see:
 - [Installing Python in Windows](https://python-docs.readthedocs.io/en/latest/starting/install3/win.html)
 - [5 Ways to Install Git on Windows](https://www.jamessturtevant.com/posts/5-Ways-to-install-git-on-Windows/)

For Mac OS X:
 - [Installing Python3 on Mac OS X](https://docs.python-guide.org/starting/install3/osx/)
 - [From: *Installing Git, the Easy Way*](https://gist.github.com/derhuerst/1b15ff4652a867391f03#step-2--install-git)

For Docker builds:
 - [See the test harness Alpine-based Dockerfile](https://github.com/Neotys-Labs/neoload-cli/blob/master/tests/docker/dind-python3/Dockerfile)

## Installation
To install, simply run the following command. As of Jan 2020, Python 2 will be permanently deprecated, therefore this utility is written for Python 3.
```
python3 -m pip install neoload
```

## Interactive CLI Help
For usage and CLI argument examples, simply run:
```
neoload --help
```

## Configuration
Before running a load test, you will need to initialize a profile to contain connection information to NeoLoad Web. Subsequent commands will use this profile unless switched to another profile, as there can be multiple. ***This is so that you only need to specify these details once only, then you can focus on validating and running load tests.***

Your profile details depend on your license model and how you want to obtain load testing resources (controller + load generators). See below:

### Create a SaaS-Based License Profile
If you have an enterprise license activated in NeoLoad Web SaaS, you do not need to specify license details in your profile. When a controller begins to run a test, it will reach out to NeoLoad Web SaaS to lease an appropriate license.
```
neoload --profile saas1 --token [NLW_TOKEN] --zone [NLW_ZONE_ID]
```

### Create a Self-Hosted Enterprise License Profile
If you do not have a SaaS-based license, you will need to specify additional licensing server url and credentials that refer to your own NeoLoad Team License Server.
```
neoload --profile nts --token [NLW_TOKEN] --zone [NLW_ZONE_ID] --ntsurl [TEAM_SERVER_URL] --ntslogin [TEAM_SERVER_USERNAME_COLON_ENC_PASS]
```

### Viewing saved profiles
You can always list profiles that have saved using the following command:
```
neoload --profiles
```
You can also view the raw/complete stored JSON representation of saved profile details using the following command:
```
neoload --profile [your_profile_name] --summary
```

### *Future* Plans to Execute Local Tests on a Free Trial License
If you do not already have an enterprise license, such as if you only have NeoLoad installed on your local workstation (from a Free Trial download or professional license), NeoLoad CLI will eventually support using your installation as an attached controller and load generator.

Additionally, if you do not have access to a dynamic infrastructure provider (i.e. OpenShift, etc.) and if you do not have Docker installed where the NeoLoad CLI is executed, your local workstation can serve as load testing resources similar to dynamic and containerized resource use cases.

This is planned to be delivered in Dec 2019.

## Running Load Tests
Once a profile is established, NeoLoad CLI makes it very easy to execute load tests. All you need is to provide an existing test suite or set of as-code file(s), then specify a scenario.

NeoLoad CLI defaults to using the NeoLoad Web APIs for Runtime operations, which means that your project assets will be zipped up together and uploaded to the NeoLoad Web deployment you specified in your profile (SaaS or self-hosted).
```
neoload --scenario sanityScenario -f [path_to_your_nlp_or_yaml_file]
```
Once a test is initialized, if you are running in interactive console mode, the NeoLoad CLI will automatically open the system default browser to your live test results.

### Obtain Basic Examples
Some basic examples are in our Git repository for this utility, under the directory ./tests/. To get them, simply clone the repo:
```
git clone https://github.com/Neotys-Labs/neoload-cli.git
```
Then, underneath this directory, you can run them simply by typing in:
```
neoload -f tests/example_2_0_runtime/default.yaml --scenario sanityScenario
```
Additionally, you can specify multiple files, such as additional SLA, variables, or servers overriding files. This works for both [.nlp] and [.yaml] files.
```
neoload -f tests/example_2_0_runtime/default.yaml -f tests/example_2_0_runtime/slas/uat.yaml --scenario sanityScenario
```

### Non-blocking Execution Workflow
You may want to manage individual steps of attaching resources, running, waiting, and detatching resources in a parallel pipeline. This is particularly useful in combination with other parallel steps that dynamically analyze SLA data and fast-fail the test (using API commands) using a known custom real-time analysis process.

The general process can be seen in the [NeoLoad CLI E2E PyTest suite](tests/test_attach_functions.py), but also abstracted below:

- Initialize a profile
  ```
  neoload --profile example --zone [static_or_dynamic_zone_id] --token [your_neoload_web_token]
  ```
- (Optional for static zone) Attach dynamic resources
  ```
  neoload --attach docker#2,neotys/neoload-loadgenerator:7.0.1
  ```
  (Note: this assumes that the host you run the above command is a Docker host or is connected to one, DinD)

- Kick off a test via NeoLoad Web Runtime
  ```
  neoload --nowait --scenario [your_scenario_name] -f [your_project_file(s)] --outfile neoload.stdout
  ```

- Grab the ID of the test just executed
  ```
  neoload --infile neoload.stdout --query testid
  ```

- (Start some other parallel operations, such as monitoring for early advanced SLA failures)

- Wait (blocking) for test to complete
  ```
  neoload --spinwait --summary --junitsla junit_neoload_sla.xml --testid [test_id_obtained_from_above_query]
  ```

- (Always) Detatch Optional Docker resources
  ```
  neoload --detatch
  ```
