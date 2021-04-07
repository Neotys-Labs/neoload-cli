import difflib
import io
import os
import re
import sys
import unicodedata

import pytest
from tests.helpers.test_utils import *

from neoload_cli_lib import displayer


@pytest.mark.results
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestDisplayer:
    def test_print_result_summary_no_sla(self, monkeypatch):
        captured_output = io.StringIO()  # Create StringIO object
        sys.stdout = captured_output  # and redirect stdout.

        json_result = json.loads(
            '{"id": "d30fdcc2-319e-4be5-818e-f1978907a3ce","name": "SLA test","description": "","author": "Anakin Skywalker","terminationReason": "POLICY","lgCount": 1,"project": "Sample_Project","scenario": "WANImpact Local","status": "TERMINATED","qualityStatus": "FAILED","startDate": 1517410739300,"endDate": 1517411040416,"duration": 301116}')
        sla_json_global = json.loads('[]')
        sla_json_test = json.loads('[]')
        sla_json_interval = json.loads('[]')
        json_stats = json.loads(
            '{"totalRequestCountSuccess": 8415,"totalRequestCountFailure": 93,"totalRequestDurationAverage": 85.36695,"totalRequestCountPerSecond": 28.254892,"totalTransactionCountSuccess": 405,"totalTransactionCountFailure": 93,"totalTransactionDurationAverage": 571.5201,"totalTransactionCountPerSecond": 1.6538477,"totalIterationCountSuccess": 77,"totalIterationCountFailure": 77,"totalGlobalDownloadedBytes": 115011235,"totalGlobalDownloadedBytesPerSecond": 381949.94,"totalGlobalCountFailure": 93}')

        displayer.print_result_summary(json_result, sla_json_global, sla_json_test, sla_json_interval, json_stats)
        ## when storing output to file ## with open("tests/resources/expected_summary_text_no_sla.txt", mode='w') as f: print(captured_output.getvalue(), file=f)
        comp = compare_texts("", "")  # initialize default for scoping
        with open("tests/resources/expected_summary_text_no_sla.txt", "r") as expected:
            comp = compare_texts(expected.read(), captured_output.getvalue())

        sys.stdout = sys.__stdout__  # Reset redirect.
        captured_output.close()

        assert comp["equivalent"], comp["details"]

    def test_print_result_summary_with_sla(self, monkeypatch):
        captured_output = io.StringIO()  # Create StringIO object
        sys.stdout = captured_output  # and redirect stdout.

        json_result = json.loads(
            '{"id": "d30fdcc2-319e-4be5-818e-f1978907a3ce","name": "SLA test","description": "","author": "Anakin Skywalker","terminationReason": "POLICY","lgCount": 1,"project": "Sample_Project","scenario": "WANImpact Local","status": "TERMINATED","qualityStatus": "FAILED","startDate": 1517410739300,"endDate": 1517411040416,"duration": 301116}')
        sla_json_global = json.loads(
            '[{"kpi": "avg-request-resp-time","status": "PASSED","value": 0.085,"warningThreshold": {"operator": ">=","value": 0.1},"failedThreshold": {"operator": ">=","value": 0.5}}]')
        sla_json_test = json.loads(
            '[{"kpi": "error-rate","status": "FAILED","value": 6.097561,"warningThreshold": {"operator": ">=","value": 2},"failedThreshold": {"operator": ">=","value": 5},"element": {"elementId": "eb1cee2c-2f37-43f7-a2bd-92cc6990f92f","name": "submit","category": "TRANSACTION","userpath": "BrowserUser_Create_report","parent": "Try"}}, {"kpi": "avg-request-per-sec","status": "WARNING","value": 12.056263,"warningThreshold": {"operator": "<=","value": 25},"element": {"elementId": "fa450a25-8880-4263-8332-81999821711e","name": "/media/js/jquery.pngFix.pack.js","category": "REQUEST","userpath": "BrowserUser_Create_report","parent": "/"}}, {"kpi": "error-rate","status": "PASSED","value": 0,"warningThreshold": {"operator": ">=","value": 2},"failedThreshold": {"operator": ">=","value": 5},"element": {"elementId": "50e8a36f-2b86-45f7-8c9c-4b7af66051b6","name": "/media/js/ushahidi.js","category": "REQUEST","userpath": "BrowserUser_Create_report","parent": "/"}}]')
        sla_json_interval = json.loads(
            '[{"kpi": "avg-resp-time","status": "FAILED","warning": 100,"warningThreshold": {"operator": ">=","value": 0.05},"failed": 23.809525,"failedThreshold": {"operator": ">=","value": 0.5},"element": {"elementId": "03f084cd-b579-4284-97fc-8901cdb9f58c","name": "/media/js/OpenLayers.js","category": "REQUEST","userpath": "BrowserUser_Create_report","parent": "/"}}, {"kpi": "avg-resp-time","status": "WARNING","warning": 7.3170733,"warningThreshold": {"operator": ">=","value": 0.05},"failed": 0,"failedThreshold": {"operator": ">=","value": 0.5},"element": {"elementId": "269a00b9-25fa-4aa5-9481-d3ffde7b2ed7","name": "/media/img/colorpicker/colorpicker_rgb_g.png","category": "REQUEST","userpath": "BrowserUser_Create_report","parent": "/media/img/icon-calendar.gif"}}, {"kpi": "error-rate","status": "PASSED","warning": 0,"warningThreshold": {"operator": ">=","value": 5},"failed": 0,"failedThreshold": {"operator": ">=","value": 10},"element": {"elementId": "b8bfc48e-b7ed-48f8-b5ea-404d3faf15cb","name": "/media/js/jquery.js","category": "REQUEST","userpath": "BrowserUser_Create_report","parent": "/"}}]')
        json_stats = json.loads(
            '{"totalRequestCountSuccess": 8415,"totalRequestCountFailure": 93,"totalRequestDurationAverage": 85.36695,"totalRequestCountPerSecond": 28.254892,"totalTransactionCountSuccess": 405,"totalTransactionCountFailure": 93,"totalTransactionDurationAverage": 571.5201,"totalTransactionCountPerSecond": 1.6538477,"totalIterationCountSuccess": 77,"totalIterationCountFailure": 77,"totalGlobalDownloadedBytes": 115011235,"totalGlobalDownloadedBytesPerSecond": 381949.94,"totalGlobalCountFailure": 93}')

        displayer.print_result_summary(json_result, sla_json_global, sla_json_test, sla_json_interval, json_stats)
        ## when storing output to file ## with open("tests/resources/expected_summary_text_with_sla.txt", mode='w') as f: print(captured_output.getvalue(), file=f)

        comp = compare_texts("", "")  # initialize default for scoping
        with open("tests/resources/expected_summary_text_with_sla.txt", "r") as expected:
            comp = compare_texts(expected.read(), captured_output.getvalue())

        sys.stdout = sys.__stdout__  # Reset redirect.
        captured_output.close()

        assert comp["equivalent"], comp["details"]

    def test_print_result_junit(self, monkeypatch):

        json_result = json.loads(
            '{"id": "d30fdcc2-319e-4be5-818e-f1978907a3ce","name": "SLA test","description": "","author": "Anakin Skywalker","terminationReason": "POLICY","lgCount": 1,"project": "Sample_Project","scenario": "WANImpact Local","status": "TERMINATED","qualityStatus": "FAILED","startDate": 1517410739300,"endDate": 1517411040416,"duration": 301116}')
        sla_json_global = json.loads(
            '[{"kpi": "avg-request-resp-time","status": "PASSED","value": 0.085,"warningThreshold": {"operator": ">=","value": 0.1},"failedThreshold": {"operator": ">=","value": 0.5}}]')
        sla_json_test = json.loads(
            '[{"kpi": "error-rate","status": "FAILED","value": 6.097561,"warningThreshold": {"operator": ">=","value": 2},"failedThreshold": {"operator": ">=","value": 5},"element": {"elementId": "eb1cee2c-2f37-43f7-a2bd-92cc6990f92f","name": "submit","category": "TRANSACTION","userpath": "BrowserUser_Create_report","parent": "Try"}}, {"kpi": "avg-request-per-sec","status": "WARNING","value": 12.056263,"warningThreshold": {"operator": "<=","value": 25},"element": {"elementId": "fa450a25-8880-4263-8332-81999821711e","name": "/media/js/jquery.pngFix.pack.js","category": "REQUEST","userpath": "BrowserUser_Create_report","parent": "/"}}, {"kpi": "error-rate","status": "PASSED","value": 0,"warningThreshold": {"operator": ">=","value": 2},"failedThreshold": {"operator": ">=","value": 5},"element": {"elementId": "50e8a36f-2b86-45f7-8c9c-4b7af66051b6","name": "/media/js/ushahidi.js","category": "REQUEST","userpath": "BrowserUser_Create_report","parent": "/"}}]')
        sla_json_interval = json.loads(
            '[{"kpi": "avg-resp-time","status": "FAILED","warning": 100,"warningThreshold": {"operator": ">=","value": 0.05},"failed": 23.809525,"failedThreshold": {"operator": ">=","value": 0.5},"element": {"elementId": "03f084cd-b579-4284-97fc-8901cdb9f58c","name": "/media/js/OpenLayers.js","category": "REQUEST","userpath": "BrowserUser_Create_report","parent": "/"}}, {"kpi": "avg-resp-time","status": "WARNING","warning": 7.3170733,"warningThreshold": {"operator": ">=","value": 0.05},"failed": 0,"failedThreshold": {"operator": ">=","value": 0.5},"element": {"elementId": "269a00b9-25fa-4aa5-9481-d3ffde7b2ed7","name": "/media/img/colorpicker/colorpicker_rgb_g.png","category": "REQUEST","userpath": "BrowserUser_Create_report","parent": "/media/img/icon-calendar.gif"}}, {"kpi": "error-rate","status": "PASSED","warning": 0,"warningThreshold": {"operator": ">=","value": 5},"failed": 0,"failedThreshold": {"operator": ">=","value": 10},"element": {"elementId": "b8bfc48e-b7ed-48f8-b5ea-404d3faf15cb","name": "/media/js/jquery.js","category": "REQUEST","userpath": "BrowserUser_Create_report","parent": "/"}}]')

        try:
            result_file_path = "tests/resources/tmp_neoload_junit_slas.xml"
            displayer.print_result_junit(json_result, sla_json_test, sla_json_interval, sla_json_global,
                                         result_file_path)

            expected_file_path = "tests/resources/expected_neoload_junit_slas.xml"
            # equivalent = main.diff_files(result_file_path, expected_file_path) == []
            diff_result = diff_file(result_file_path, expected_file_path)

        finally:
            os.unlink(result_file_path)

        sys.stdout = sys.__stdout__  # Reset redirect.

        print('\n'.join(diff_result))
        assert list(diff_result) == []


def diff_file(file1, file2):
    text1 = open(file1).readlines()
    text2 = open(file2).readlines()
    return difflib.unified_diff(text1, text2)


# created to handle color control characters; == equivalency is too strict
def compare_texts(a, b):
    ret = {
        "equivalent": True,
        "details": ""
    }
    a_re = remove_color_indicators(a)
    b_re = remove_color_indicators(b)
    for i, s in enumerate(difflib.ndiff(a_re, b_re)):
        w = remove_control_characters(s[-1]).strip()
        if s[0] == ' ':
            continue
        elif s[0] == '-':
            ret["details"] += u'Delete "{}" from position {}'.format(s[-1], i)
        elif s[0] == '+':
            ret["details"] += u'Add "{}" to position {}'.format(s[-1], i)
        if s[0] in ['-', '+'] and len(w) > 0:
            ret["equivalent"] = False
            ret["details"] += w + ":"
            break
    return ret


def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")


def remove_color_indicators(s):
    return re.sub(r'(\[[0123456789]{1,2}m)', '', s)
