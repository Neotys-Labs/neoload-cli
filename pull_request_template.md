## What?
[A description of what module or functionality is being proposed and what user outcome is expected]

*EXAMPLE: "Update to get_with_pagination and ls functions to support more precise filtering of JSON results from the REST API."*

## Why?
[More detail on why this change is impactful to user, details on the use case and in real usage scenario, how does this improve what currently exists]

*EXAMPLE: "In a real system, the 'test-results ls' command may come back with thousands of results, which is typically not the intent of the calling process. 
Usually, there is more of a precise context for what is being searched for, such as test results by project name, scenario, status, or qualityStatus. 
Therefore, and easy way to filter output, and where possible do this by providing the API endpoint matching parameters to let the API do the work, is needed."*

## How?
[Details on the approach taken in implementation that produces the outcome, why specific files/modules were changed in this process]

*EXAMPLE: "Update existing logic to include --filter "project=MyProject;scenario=MyScenario", such that the project parameter is used in the API call. 
Other parameters, such as the scenario value (which isn't currently supported as an API param) should be used after pagination against resulting entities whose properties identified by the key values match their corresponding filter values. 
Values can use regex or a wildcard-star character. Multiple filters shall be delimited by the pipe (priority) or semicolon character and shall be treated as AND exclusive (multiple filters must all be matched)."*

## Testing
[What was done to verify that this change not only works as designed, but also doesn't introduce any regression issues in other modules]

*EXAMPLE: "Tested locally against SaaS CPV data and added tests/commands/test_results/test_result_ls.py::TestResultLs::test_list_filter"*

## Additional Notes
[Any other detail that other team members might need to understand so that approving this PR is as easy as possible]

*EXAMPLE: "Due to the nature of monkeypatch and optional parameter support, in order to remain compatible to both real and mock fixtures, this had to be implemented to use filtering.set_filter before and filtering.clear_filter after the call. 
Use of filtering.remove_by_last_filter in the tools.ls command ensures that tests also exercise the post-processing filters, not simply when real API data is used."*
