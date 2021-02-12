import pytest

from commands import report


@pytest.mark.report
class TestReport:
    def test_initialize_model_empty(self):
        model = report.initialize_model("", "")
        assert model == {'components':
                             {'all_requests': True,
                              'controller_points': True,
                              'events': True,
                              'ext_data': True,
                              'monitors': True,
                              'slas': True,
                              'statistics': True,
                              'summary': True,
                              'transactions': True},
                         'filter_spec':
                             {'elements_filter': None,
                              'exclude_filter': None,
                              'include_filter': None,
                              'results_filter': None,
                              'time_filter': None}
                         }

    def test_initialize_model_transactions(self):
        model = report.initialize_model("", "builtin:transactions")
        assert model == {'components':
                             {'all_requests': False,
                              'controller_points': False,
                              'events': False,
                              'ext_data': False,
                              'monitors': False,
                              'slas': False,
                              'statistics': False,
                              'summary': True,
                              'transactions': True},
                         'filter_spec':
                             {'elements_filter': None,
                              'exclude_filter': None,
                              'include_filter': None,
                              'results_filter': None,
                              'time_filter': None}
                         }

    # TODO uncomment and fix these unit tests
    # def test_initialize_model_excludes(self):
    #     model = report.initialize_model("timespan=8-10;results=-2;excludes=events,slas;elements=TransactionName", "")
    #     assert model == {'components':
    #                          {'all_requests': True,
    #                           'controller_points': True,
    #                           'events': False,
    #                           'ext_data': True,
    #                           'monitors': True,
    #                           'slas': False,
    #                           'statistics': True,
    #                           'summary': True,
    #                           'transactions': True},
    #                      'filter_spec':
    #                          {'elements_filter': 'TransactionName',
    #                           'exclude_filter': 'excludes=events,slas',
    #                           'include_filter': None,
    #                           'results_filter': '-2',
    #                           'time_filter': '8-10'}
    #                       }
    #
    # def test_initialize_model_includes(self):
    #     model = report.initialize_model("timespan=8-10;results=-2;includes=events,controller_points,slas;elements=TransactionName", "")
    #     assert model == {'components':
    #                          {'all_requests': False,
    #                           'controller_points': True,
    #                           'events': True,
    #                           'ext_data': False,
    #                           'monitors': False,
    #                           'slas': True,
    #                           'statistics': False,
    #                           'summary': True,
    #                           'transactions': True},
    #                      'filter_spec':
    #                          {'elements_filter': 'TransactionName',
    #                           'exclude_filter': None,
    #                           'include_filter': 'includes=events,slas',
    #                           'results_filter': '-2',
    #                           'time_filter': '8-10'}
    #                      }

    def test_initialize_model_csv(self):
        model = report.initialize_model(
            "timespan=8-10;results=-2;excludes=transactions;includes=requests;elements=TransactionName",
            "builtin:transactions-csv")
        assert model == {'components':
                             {'all_requests': False,
                              'controller_points': False,
                              'events': False,
                              'ext_data': False,
                              'monitors': False,
                              'slas': False,
                              'statistics': False,
                              'summary': True,
                              'transactions': True},
                         'filter_spec':
                             {'elements_filter': 'TransactionName',
                              'exclude_filter': 'excludes=transactions',
                              'include_filter': 'includes=requests',
                              'results_filter': '-2',
                              'time_filter': '8-10'},
                         'template_text': """User Path;Element;Parent;Count;Min;Avg;Max;Perc 50;Perc 90;Perc 95;Perc 99;Success;Success Rate;Failure;Failure Rate{%
    for txn in elements.transactions | rejectattr('id', 'equalto', 'all-transactions') | rejectattr('aggregate.count', 'equalto', 0) | sort(attribute='avgDuration',reverse=true) %}
{{ txn.user_path|e }};{{ txn.name|e }};{{ txn.parent|e }};{{ txn.aggregate.count }};{{ txn.aggregate.minDuration }};{{ txn.aggregate.avgDuration }};{{ txn.aggregate.maxDuration }};{{ txn.aggregate.percentile50 }};{{ txn.aggregate.percentile90 }};{{ txn.aggregate.percentile95 }};{{ txn.aggregate.percentile99 }};{{ txn.aggregate.successCount }};{{ txn.aggregate.successRate }};{{ txn.aggregate.failureCount }};{{ txn.aggregate.failureRate }}{%
    endfor %}"""}

    def test_initialize_model_console(self):
        model = report.initialize_model(
            "timespan=8-10;results=-2;excludes=transactions;includes=requests;elements=TransactionName",
            "builtin:console-summary")
        assert model == {'components':
                             {'all_requests': False,
                              'controller_points': False,
                              'events': False,
                              'ext_data': False,
                              'monitors': False,
                              'slas': True,
                              'statistics': True,
                              'summary': True,
                              'transactions': True},
                         'filter_spec':
                             {'elements_filter': 'TransactionName',
                              'exclude_filter': 'excludes=transactions',
                              'include_filter': 'includes=requests',
                              'results_filter': '-2',
                              'time_filter': '8-10'},
                         'template_text': """Test Name: {{summary.name}}
Start: {{summary.startDateText}}	Duration: {{summary.durationText}}
End: {{summary.endDateText}}	Execution Status: {{summary.status}} by {{summary.terminationReason}}
Description: {{summary.description}}
Project: {{summary.project}}
Scenario: {{summary.scenario}}
Quality Status: {{summary.qualityStatus}}

Transactions summary:
User Path	Element	Count	Min	Avg	Max	Perc 50	Perc 90	Perc 95	Perc 99	Success	S.Rate	Failure	F.Rate
{% for txn in elements.transactions | rejectattr('id', 'equalto', 'all-transactions') | rejectattr('aggregate.count', 'equalto', '0') | sort(attribute='avgDuration',reverse=true)
%}{{ txn.user_path|e }}	{{ txn.name|e }}	{{ txn.aggregate.count }}	{{ txn.aggregate.minDuration }}	{{ txn.aggregate.avgDuration }}	{{ txn.aggregate.maxDuration }}	{{ txn.aggregate.percentile50 }}	{{ txn.aggregate.percentile90 }}	{{ txn.aggregate.percentile95 }}	{{ txn.aggregate.percentile99 }}	{{ txn.aggregate.successCount }}	{{ txn.aggregate.successRate }}	{{ txn.aggregate.failureCount }}	{{ txn.aggregate.failureRate }}
{% endfor %}"""
                         }
