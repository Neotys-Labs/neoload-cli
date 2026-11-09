# Contributing

Feel free to fork this repo, make your changes, *test locally*, and then open a pull request.

## Local verification

### Tests
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

## Release process (managed by the Tricentis NeoLoad team)

### Auto-generating the changelog

Before tagging a release, merged PRs should update `CHANGELOG.md` using the following command:

```
github_changelog_generator -u Neotys-Labs -p neoload-cli --token $GIT_CHANGELOG_GEN --exclude-tags-regex ".*(dev|rc).*" --add-sections '{"documentation":{"prefix":"**Documentation updates:**","labels":["documentation"]}}'
```

This utility is a [Ruby-based gem](https://github.com/github-changelog-generator/github-changelog-generator) (also used in CI/Actions) that can be installed with:

```
gem install github_changelog_generator
```

### Version management on PyPI
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
