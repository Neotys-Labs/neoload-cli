# NeoLoad CLI

This command-line interface helps you launch and observe performance tests on the Neotys Platform. Since NeoLoad is very flexible to many deployment models (SaaS, self-hosted, cloud or local containers, etc.), configuration and test execution parameters depend on your licensing and infrastructure provisioning options. Please read the following instructions carefully.

 - [Prerequisites](#prerequisites)
 - [Installation](#installation)
 - [Configuration](#configuration)
 - [Running Load Tests](#running-load-tests)
 - [Additional Options](#additional-options)
    - [Exporting SLA Results to JUnit](#exporting-sla-results-to-junit)
    - [Test Summary](#test-summary)
    - [Test Modifications](#test-modifications)
 - [Contributing](#contributing)

## Prerequisites
The examples below assume that you have Python3 and Git command line tools installed.

For **Windows 10 users**, see:
 - [Installing Python in Windows](https://python-docs.readthedocs.io/en/latest/starting/install3/win.html)
   In short:
    - Just install via [Python.org Downloads](https://www.python.org/downloads/), then
    - Open a command prompt and install pip:
        ```
        python -m pip install -U pip
        ```
 - [5 Ways to Install Git on Windows](https://www.jamessturtevant.com/posts/5-Ways-to-install-git-on-Windows/)
 - Install Docker with Chocolatey
    - [Install Chocolatey package manager for Windows](https://chocolatey.org/docs/installation)
    - Open a command prompt and install Docker Desktop for Windows 10
        ```
        choco install docker-cli docker-desktop
        ```

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
## Additional Options
There are many other arguments for test summarization, modification, and exporting results.

### Using more than one Controller and Load Generator from a zone
Presuming that you already have a zone with available resources in it, you can specify
 to use more than one load generator. The zone should be stored in your current profile.
```
  neoload --attach zone#3 -f tests/example_2_0_runtime/default.yaml --scenario sanityScenario
```
...where the number three is the number of available load generators you want this test to utilize.

### Exporting SLA Results to JUnit
```
  neoload --testid [guid] --junitsla=junit_sla_results.xml
```
### Verbose and Debug Mode
Verbose mode changes logging level to INFO. When executing from an interactive console, it also opens a browser window to the test logs immediately after they're available (useful for monitoring the infrastructure initialization process).
```
neoload -f tests/example_2_0_runtime/default.yaml --scenario sanityScenario --verbose
```
Debug mode changes logging level to DEBUG. This is an extreme amount of internal information which infers verbose/INFO mode and provides manual pausing on critical events (such as after Docker attach but before test execution).
```
neoload -f tests/example_2_0_runtime/default.yaml --scenario sanityScenario --debug
```
### Quiet Mode
Adding the *--quiet* flag generally produces only the relevant output (i.e. JSON, test id, etc.) and no other informational messages. This is useful when piping the structured data output into another process, such as obtaining the most recent test id from stdout file (*--quiet* is inferred by some other combinations of flags such as *--infile* AND *--query testid*).

### Test Summary
Specifying both a *--testid* value and the *--summary* flag produces a JSON result set that shows both the high level test status metadata and overall statistics.
```
neoload --testid c9f9c994-da31-4b63-b622-42a80e313d15 --summary --quiet
```
Produces:
```
{
	'summary':{
		'author':'Paul Bruce',
		'description':'',
		'duration':10921,
		'end_date':1575675769036,
		'id':'c9f9c994-da31-4b63-b622-42a80e313d15',
		'lg_count':1,
		'name':'NeoLoad-CLI-example-2_0_sanityScenario',
		'project':'NeoLoad-CLI-example-2_0',
		'quality_status':'FAILED',
		'scenario':'sanityScenario',
		'start_date':1575675758115,
		'status':'TERMINATED',
		'termination_reason':'POLICY'
	},
	'statistics':{
		'last_request_count_per_second':None,
		'last_transaction_duration_average':None,
		'last_virtual_user_count':None,
		'total_global_count_failure':0,
		'total_global_downloaded_bytes':97876,
		'total_global_downloaded_bytes_per_second':8962.183,
		'total_iteration_count_failure':0,
		'total_iteration_count_success':10,
		'total_request_count_failure':0,
		'total_request_count_per_second':1.0988004,
		'total_request_count_success':12,
		'total_request_duration_average':495.75,
		'total_transaction_count_failure':0,
		'total_transaction_count_per_second':1.0072337,
		'total_transaction_count_success':11,
		'total_transaction_duration_average':496.9091
	}
```
*TODO: This summary will also include SLA summaries in Jan 2020*
### Test Modifications
Metadata on a test can be modified after the test is complete, such as name, description, and status. With the required *--testid* argument as well, these modification arguments can be used individually or in combination with each other.
```
neoload --testid [test id] --updatename 'Some new test name' --updatedesc 'Some new description' --updatestatus 'PASSED|FAILED'
```
Additionally, plus and minus (+/-) operators can be used to append or remove the text specified from the existing name or description data. This is useful in combination with hashtag keywords to flag a test as baseline, candidate, or with an issue tracking id.
```
neoload --testid [old baseline test id] --updatedesc '-#baseline'
neoload --testid [new test id] --updatedesc '+#baseline'
```

### Test Result listings and queries
*TODO: will be coming in Jan 2020*

## Contributing
Feel free to fork this repo, make changes, *test locally*, and create a pull request. As part of your testing, you should run the built-in test suite with the following command:
```
python3 -m pytest -v tests
```
*NOTE: omitting the --skipslow and --skipslas arguments also runs Docker-related attaching tests, which you will need to set environment variables up for in order to successfully run the test suite. An example of these variables can be found in [example.bash_profile](tests/example.bash_profile) and can be addapted for Windows execution as well.
