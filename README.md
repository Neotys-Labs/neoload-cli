# NeoLoad CLI

This command-line interface helps you launch and observe performance tests on the Neotys Platform. Since NeoLoad is very flexible to many deployment models (SaaS, self-hosted, cloud or local containers, etc.), configuration and test execution parameters depend on your licensing and infrastructure provisioning options. Please read the following instructions carefully.

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
neoload --profile nts --token [NLW_TOKEN] --zone [NLW_ZONE_ID] --nts-url [TEAM_SERVER_URL] --nts-credentials [TEAM_SERVER_USERNAME_ENC_PASS]
```

### *Future* Plans to Execute Local Tests on a Free Trial License
If you do not already have an enterprise license, such as if you only have NeoLoad installed on your local workstation (from a Free Trial download or professional license), NeoLoad CLI will eventually support using your installation as an attached controller and load generator.

Additionally, if you do not have access to a dynamic infrastructure provider (i.e. OpenShift, etc.) and if you do not have Docker installed where the NeoLoad CLI is executed, your local workstation can serve as load testing resources similar to dynamic and containerized resource use cases.

This is planned to be delivered in Dec 2019.

## Running Load Tests
Once a profile is established, NeoLoad CLI makes it very easy to execute load tests. All you need is to provide an existing test suite or set of as-code file(s), then specify a scenario.

NeoLoad CLI defaults to using the NeoLoad Web APIs for Runtime operations, which means that your project assets will be zipped up together and uploaded to the NeoLoad Web deployment you specified in your profile (SaaS or self-hosted).

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
