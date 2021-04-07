# Changelog

## [1.3.2](https://github.com/Neotys-Labs/neoload-cli/tree/1.3.2) (2021-04-07)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.3.1...1.3.2)

**Fixed bugs:**

- Fix test mod refs [\#168](https://github.com/Neotys-Labs/neoload-cli/pull/168) ([paulsbruce](https://github.com/paulsbruce))

**Documentation updates:**

- Auto-generate CHANGELOG after tag 1.3.1 [\#166](https://github.com/Neotys-Labs/neoload-cli/pull/166) ([github-actions[bot]](https://github.com/apps/github-actions))

## [1.3.1](https://github.com/Neotys-Labs/neoload-cli/tree/1.3.1) (2021-04-06)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.3.0...1.3.1)

**Fixed bugs:**

- Update fastfail and SLA report, warning are not failures [\#145](https://github.com/Neotys-Labs/neoload-cli/pull/145) ([paulsbruce](https://github.com/paulsbruce))
- Fix report 00184240 [\#143](https://github.com/Neotys-Labs/neoload-cli/pull/143) ([paulsbruce](https://github.com/paulsbruce))
- Convert entity property values to string before filter compare [\#133](https://github.com/Neotys-Labs/neoload-cli/pull/133) ([paulsbruce](https://github.com/paulsbruce))
- Fix trends back/ahead result selection logic [\#132](https://github.com/Neotys-Labs/neoload-cli/pull/132) ([paulsbruce](https://github.com/paulsbruce))

**Documentation updates:**

- fix\(doc\): Issues with gitlab openshit CI examples [\#141](https://github.com/Neotys-Labs/neoload-cli/pull/141) ([TanguyBaudrin](https://github.com/TanguyBaudrin))
- Update changelog with auto-generated details; old one only went to 1.… [\#137](https://github.com/Neotys-Labs/neoload-cli/pull/137) ([paulsbruce](https://github.com/paulsbruce))

**Merged pull requests:**

- Finalize CHANGELOG workflow [\#164](https://github.com/Neotys-Labs/neoload-cli/pull/164) ([paulsbruce](https://github.com/paulsbruce))
- Make status human readable [\#150](https://github.com/Neotys-Labs/neoload-cli/pull/150) ([paulsbruce](https://github.com/paulsbruce))
- Improve builtin templates [\#149](https://github.com/Neotys-Labs/neoload-cli/pull/149) ([paulsbruce](https://github.com/paulsbruce))
- Add more granular Docker checks [\#148](https://github.com/Neotys-Labs/neoload-cli/pull/148) ([paulsbruce](https://github.com/paulsbruce))
- Add docker coverage [\#147](https://github.com/Neotys-Labs/neoload-cli/pull/147) ([paulsbruce](https://github.com/paulsbruce))
- Sonar updates [\#146](https://github.com/Neotys-Labs/neoload-cli/pull/146) ([paulsbruce](https://github.com/paulsbruce))
- Fix validate command from as-code training outcomes [\#144](https://github.com/Neotys-Labs/neoload-cli/pull/144) ([paulsbruce](https://github.com/paulsbruce))
- Update ls to use internal filtering b/c endpoint not implemented; tes… [\#142](https://github.com/Neotys-Labs/neoload-cli/pull/142) ([paulsbruce](https://github.com/paulsbruce))

## [1.3.0](https://github.com/Neotys-Labs/neoload-cli/tree/1.3.0) (2021-03-18)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.2.1...1.3.0)

**Implemented enhancements:**

- Add Docker command [\#124](https://github.com/Neotys-Labs/neoload-cli/pull/124) ([neotys-rd](https://github.com/neotys-rd))

**Closed issues:**

- Issue project upload on current directory [\#125](https://github.com/Neotys-Labs/neoload-cli/issues/125)

**Merged pull requests:**

- Revert "Explain which file is empty" [\#136](https://github.com/Neotys-Labs/neoload-cli/pull/136) ([stephanemartin](https://github.com/stephanemartin))
- Fix test [\#135](https://github.com/Neotys-Labs/neoload-cli/pull/135) ([stephanemartin](https://github.com/stephanemartin))
- Explain which file is empty [\#134](https://github.com/Neotys-Labs/neoload-cli/pull/134) ([stephanemartin](https://github.com/stephanemartin))
- Add QA scripts to test the CLI on a real NLW [\#131](https://github.com/Neotys-Labs/neoload-cli/pull/131) ([guillaumebert](https://github.com/guillaumebert))
- Add manual pipeline for integration tests [\#130](https://github.com/Neotys-Labs/neoload-cli/pull/130) ([guillaumebert](https://github.com/guillaumebert))

## [1.2.1](https://github.com/Neotys-Labs/neoload-cli/tree/1.2.1) (2021-03-01)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.2.0...1.2.1)

**Implemented enhancements:**

- Auto refresh schema if possible; allow whole directory validation [\#127](https://github.com/Neotys-Labs/neoload-cli/pull/127) ([paulsbruce](https://github.com/paulsbruce))

**Fixed bugs:**

- Fixbug \#125 currend directory issue on neoload project upload. [\#126](https://github.com/Neotys-Labs/neoload-cli/pull/126) ([neotys-rd](https://github.com/neotys-rd))

**Merged pull requests:**

- Set command for report command user agent [\#129](https://github.com/Neotys-Labs/neoload-cli/pull/129) ([guillaumebert](https://github.com/guillaumebert))

## [1.2.0](https://github.com/Neotys-Labs/neoload-cli/tree/1.2.0) (2021-02-18)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.1.8...1.2.0)

**Implemented enhancements:**

- Add custom command support to fastfail [\#122](https://github.com/Neotys-Labs/neoload-cli/pull/122) ([paulsbruce](https://github.com/paulsbruce))
- Add --save path argument to upload command [\#117](https://github.com/Neotys-Labs/neoload-cli/pull/117) ([paulsbruce](https://github.com/paulsbruce))
- Add global config feature [\#115](https://github.com/Neotys-Labs/neoload-cli/pull/115) ([stephanemartin](https://github.com/stephanemartin))
- Topic report command [\#107](https://github.com/Neotys-Labs/neoload-cli/pull/107) ([paulsbruce](https://github.com/paulsbruce))

**Closed issues:**

- Error during the Get junit SLA report [\#116](https://github.com/Neotys-Labs/neoload-cli/issues/116)

**Merged pull requests:**

- Add interactive or automated information to UserAgent header [\#123](https://github.com/Neotys-Labs/neoload-cli/pull/123) ([guillaumebert](https://github.com/guillaumebert))
- Fix user agent header value when chaining commands [\#121](https://github.com/Neotys-Labs/neoload-cli/pull/121) ([guillaumebert](https://github.com/guillaumebert))
- Improve unit testing - createorpatch command [\#120](https://github.com/Neotys-Labs/neoload-cli/pull/120) ([guillaumebert](https://github.com/guillaumebert))
- Compute version in tools.py to make it available to other commands [\#119](https://github.com/Neotys-Labs/neoload-cli/pull/119) ([guillaumebert](https://github.com/guillaumebert))
- Fix typo in error message when not logged in. [\#118](https://github.com/Neotys-Labs/neoload-cli/pull/118) ([guillaumebert](https://github.com/guillaumebert))

## [1.1.8](https://github.com/Neotys-Labs/neoload-cli/tree/1.1.8) (2020-12-04)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.1.7...1.1.8)

**Merged pull requests:**

- Remove pyparsing dependency [\#113](https://github.com/Neotys-Labs/neoload-cli/pull/113) ([paulsbruce](https://github.com/paulsbruce))

## [1.1.7](https://github.com/Neotys-Labs/neoload-cli/tree/1.1.7) (2020-12-04)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.1.6...1.1.7)

**Implemented enhancements:**

- Retry after the specified delay when NLW rate limit is reached [\#111](https://github.com/Neotys-Labs/neoload-cli/pull/111) ([guillaumebert](https://github.com/guillaumebert))

**Merged pull requests:**

- Add 'pyparsing' to setup dependencies, tested/working in Jenkinsfile\_… [\#112](https://github.com/Neotys-Labs/neoload-cli/pull/112) ([paulsbruce](https://github.com/paulsbruce))
- Add github actions for package and release on pypi [\#108](https://github.com/Neotys-Labs/neoload-cli/pull/108) ([guillaumebert](https://github.com/guillaumebert))

## [1.1.6](https://github.com/Neotys-Labs/neoload-cli/tree/1.1.6) (2020-12-03)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.1.5...1.1.6)

**Documentation updates:**

- Update CHANGELOG.md [\#110](https://github.com/Neotys-Labs/neoload-cli/pull/110) ([stephanemartin](https://github.com/stephanemartin))
- Create default PR template [\#106](https://github.com/Neotys-Labs/neoload-cli/pull/106) ([paulsbruce](https://github.com/paulsbruce))
- Version management on pypi in readme [\#105](https://github.com/Neotys-Labs/neoload-cli/pull/105) ([guillaumebert](https://github.com/guillaumebert))

**Closed issues:**

- No Result Found to Publish : SLA Reporting via JUnit  [\#99](https://github.com/Neotys-Labs/neoload-cli/issues/99)

**Merged pull requests:**

- Define test requirements in a separate file [\#109](https://github.com/Neotys-Labs/neoload-cli/pull/109) ([guillaumebert](https://github.com/guillaumebert))

## [1.1.5](https://github.com/Neotys-Labs/neoload-cli/tree/1.1.5) (2020-11-10)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.1.4...1.1.5)

**Implemented enhancements:**

- Filtering for ls-related commands [\#102](https://github.com/Neotys-Labs/neoload-cli/pull/102) ([paulsbruce](https://github.com/paulsbruce))
- Update largefile upload [\#91](https://github.com/Neotys-Labs/neoload-cli/pull/91) ([paulsbruce](https://github.com/paulsbruce))

**Documentation updates:**

- Review of documentation [\#103](https://github.com/Neotys-Labs/neoload-cli/pull/103) ([guillaumebert](https://github.com/guillaumebert))
- Improve Readme [\#101](https://github.com/Neotys-Labs/neoload-cli/pull/101) ([guillaumebert](https://github.com/guillaumebert))
- Add bamboo pipeline example [\#100](https://github.com/Neotys-Labs/neoload-cli/pull/100) ([guillaumebert](https://github.com/guillaumebert))

**Closed issues:**

- Error 500 with cli-python and dynamic Infrastructure \(Pipeline yaml Azure DevOps\) [\#95](https://github.com/Neotys-Labs/neoload-cli/issues/95)

**Merged pull requests:**

- Add global SLAs \(test\) [\#104](https://github.com/Neotys-Labs/neoload-cli/pull/104) ([ceimard-neo](https://github.com/ceimard-neo))

## [1.1.4](https://github.com/Neotys-Labs/neoload-cli/tree/1.1.4) (2020-09-25)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.1.3...1.1.4)

**Implemented enhancements:**

- Add 'cur' pseudonym support to logs-url [\#98](https://github.com/Neotys-Labs/neoload-cli/pull/98) ([stephanemartin](https://github.com/stephanemartin))
- Add capability to manage self signed certificate [\#94](https://github.com/Neotys-Labs/neoload-cli/pull/94) ([stephanemartin](https://github.com/stephanemartin))
- Update to use master branch and include --lgs [\#93](https://github.com/Neotys-Labs/neoload-cli/pull/93) ([paulsbruce](https://github.com/paulsbruce))
- Topic upload .nlignore [\#90](https://github.com/Neotys-Labs/neoload-cli/pull/90) ([paulsbruce](https://github.com/paulsbruce))

**Fixed bugs:**

- Remove timeout for bigfile and slow server [\#97](https://github.com/Neotys-Labs/neoload-cli/pull/97) ([stephanemartin](https://github.com/stephanemartin))

**Documentation updates:**

- Add AWS CodeBuild example pipeline [\#84](https://github.com/Neotys-Labs/neoload-cli/pull/84) ([paulsbruce](https://github.com/paulsbruce))

## [1.1.3](https://github.com/Neotys-Labs/neoload-cli/tree/1.1.3) (2020-08-19)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.1.2...1.1.3)

## [1.1.2](https://github.com/Neotys-Labs/neoload-cli/tree/1.1.2) (2020-08-18)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.1.0...1.1.2)

## [1.1.0](https://github.com/Neotys-Labs/neoload-cli/tree/1.1.0) (2020-08-11)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.0.1...1.1.0)

**Implemented enhancements:**

- Topic pagination [\#89](https://github.com/Neotys-Labs/neoload-cli/pull/89) ([guillaumebert](https://github.com/guillaumebert))
- Topic workspace compatibility [\#85](https://github.com/Neotys-Labs/neoload-cli/pull/85) ([guillaumebert](https://github.com/guillaumebert))
- Topic fastfail command [\#73](https://github.com/Neotys-Labs/neoload-cli/pull/73) ([paulsbruce](https://github.com/paulsbruce))

**Fixed bugs:**

- Fix the bug : Run a test and specify the scenario [\#77](https://github.com/Neotys-Labs/neoload-cli/pull/77) ([guillaumebert](https://github.com/guillaumebert))

**Documentation updates:**

- Fix issue on sample Jenkinsfile [\#76](https://github.com/Neotys-Labs/neoload-cli/pull/76) ([stephanemartin](https://github.com/stephanemartin))
- Add as-code schema to keep compatibility with CLI v0 [\#70](https://github.com/Neotys-Labs/neoload-cli/pull/70) ([guillaumebert](https://github.com/guillaumebert))

**Closed issues:**

- Cli Crash when Neoload Web doesn't give one value. [\#74](https://github.com/Neotys-Labs/neoload-cli/issues/74)

**Merged pull requests:**

- Miscellaneous improvements [\#86](https://github.com/Neotys-Labs/neoload-cli/pull/86) ([stephanemartin](https://github.com/stephanemartin))
- Add 'certifi' install prerequisite [\#78](https://github.com/Neotys-Labs/neoload-cli/pull/78) ([paulsbruce](https://github.com/paulsbruce))

## [1.0.1](https://github.com/Neotys-Labs/neoload-cli/tree/1.0.1) (2020-06-25)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/1.0.0...1.0.1)

**Fixed bugs:**

- Fix issue \#74 [\#75](https://github.com/Neotys-Labs/neoload-cli/pull/75) ([stephanemartin](https://github.com/stephanemartin))

**Closed issues:**

- tests failing on master with python3.6 [\#65](https://github.com/Neotys-Labs/neoload-cli/issues/65)

**Merged pull requests:**

- update setup with minimum versions [\#71](https://github.com/Neotys-Labs/neoload-cli/pull/71) ([adamleskis](https://github.com/adamleskis))

## [1.0.0](https://github.com/Neotys-Labs/neoload-cli/tree/1.0.0) (2020-05-14)

[Full Changelog](https://github.com/Neotys-Labs/neoload-cli/compare/be4a5ffb33d78b882da89705636176737114f389...1.0.0)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
