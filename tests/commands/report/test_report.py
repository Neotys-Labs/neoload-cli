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

    def test_initialize_model_excludes(self):
        model = report.initialize_model("timespan=8-10;results=-2;excludes=events,slas;elements=TransactionName", "")
        assert model == {'components':
                             {'all_requests': True,
                              'controller_points': True,
                              'events': False,
                              'ext_data': True,
                              'monitors': True,
                              'slas': False,
                              'statistics': True,
                              'summary': True,
                              'transactions': True},
                         'filter_spec':
                             {'elements_filter': 'TransactionName',
                              'exclude_filter': 'events,slas',
                              'include_filter': None,
                              'results_filter': '-2',
                              'time_filter': '8-10'}
                         }

    def test_initialize_model_includes(self):
        model = report.initialize_model(
            "timespan=8-10;results=-2;includes=events,controller_points,slas;elements=TransactionName", "")
        assert model == {'components':
                             {'all_requests': False,
                              'controller_points': True,
                              'events': True,
                              'ext_data': False,
                              'monitors': False,
                              'slas': True,
                              'statistics': False,
                              'summary': True,
                              'transactions': False},
                         'filter_spec':
                             {'elements_filter': 'TransactionName',
                              'exclude_filter': None,
                              'include_filter': 'events,controller_points,slas',
                              'results_filter': '-2',
                              'time_filter': '8-10'}
                         }

    def test_initialize_model_includes_and_excludes(self):
        model = report.initialize_model(
            "timespan=8-10;results=-2;excludes=ext_data;includes=events,slas;elements=TransactionName", "")
        assert model == {'components':
                             {'all_requests': False,
                              'controller_points': False,
                              'events': True,
                              'ext_data': False,
                              'monitors': False,
                              'slas': True,
                              'statistics': False,
                              'summary': True,
                              'transactions': False},
                         'filter_spec':
                             {'elements_filter': 'TransactionName',
                              'exclude_filter': 'ext_data',
                              'include_filter': 'events,slas',
                              'results_filter': '-2',
                              'time_filter': '8-10'}
                         }

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
                              'exclude_filter': 'transactions',
                              'include_filter': 'requests',
                              'results_filter': '-2',
                              'time_filter': '8-10'},
                         'template_text': report.get_builtin_template_transaction_csv()
                         }

    def test_initialize_model_console(self):
        model = report.initialize_model(
            "timespan=8-10;results=-2;excludes=transactions;includes=all_requests;elements=TransactionName",
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
                              'exclude_filter': 'transactions',
                              'include_filter': 'all_requests',
                              'results_filter': '-2',
                              'time_filter': '8-10'},
                         'template_text': report.get_builtin_template_console_summary()
                         }

    def test_fill_time_binding(self):
        # Test absolute times
        assert_time_binding_from_to('1m-2m', 60, 120)
        assert_time_binding_from_to('1h5m30s-90m120s', 3930, 5520)
        assert_time_binding_from_to('10m', 600, 121)
        assert_time_binding_from_to('-10m', 0, 600)

        # Test percentage of test duration (test lasts 120 sec)
        assert_time_binding_from_to('10%-62%', 12, 75)
        assert_time_binding_from_to('30%', 36, 121)
        assert_time_binding_from_to('-30%', 0, 37)

        # Mix
        assert_time_binding_from_to('10m-62%', 600, 75)

    def test_filter_by_time(self):
        json_points = [{'from': 10, 'to': 20}, {'from': 10, 'to': 130}, {'from': 120, 'to': 130},
                       {'from': 10, 'to': 300}, {'from': 120, 'to': 300}, {'from': 250, 'to': 300}]
        time_binding = {
            'from_secs': 100,
            'to_secs': 200
        }
        filtered_json_points = report.filter_by_time(json_points, time_binding, lambda p: int(p['from']),
                                                     lambda p: int(p['to']))
        assert filtered_json_points == [{'from': 120, 'to': 130}]


def assert_time_binding_from_to(time_filter, expected_from_secs, expected_to_secs):
    time_binding = report.fill_time_binding({
        'time_filter': time_filter,
        'summary': {"duration": 120144}
    })
    assert time_binding['from_secs'] == expected_from_secs
    assert time_binding['to_secs'] == expected_to_secs
