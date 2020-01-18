from neoload import *

import logging
import pprint
import sys
from pprint import pprint
from io import open
from junit_xml import TestSuite, TestCase

# <testsuite name="com.neotys.sla_external_api_calls.PerRun.api_savedsearch">
#       <testcase end="2" name="test_PercentileTr_nResponseTime1" result="success" start="1">
#          <success type="NeoLoad SLA"> everything is fine </success>
#       </testcase>
#    </testsuite>
#    <testsuite name="com.neotys.sla_internal_api_calls.PerRun.api_savedsearch">
#       <testcase end="2" name="test_AverageReque_tResponseTime1" result="failure" start="1">
#          <failure type="NeoLoad SLA">
# Container: /platform/oauth/token
# Path: User Paths =&gt; api_savedsearch =&gt; Init =&gt; Obtain OAuth Token =&gt; /platform/oauth/token
# Virtual User: api_savedsearch
# SLA Profile: sla_internal_api_calls
# SLA Type: Per Run
# Alert Type: Average Request Response Time
# Project: CPVWeatherCrisis
# Scenario: dynAPISanityCheck
#
# Alert description:
#
# if the
# 	 Average Request Response Time &gt;= 1.0
# then
# 	 fail
#
# Results:
#
# Average Request Response Time = 1.317
#
# Created 2019-11-22 19:48:01 </failure>
#       </testcase>
#    </testsuite>

# {
#     "kpi": "avg-request-resp-time",
#     "status": "FAILED",
#     "value": 1.317,
#     "warningThreshold": {
#       "operator": ">=",
#       "value": 0.5
#     },
#     "failedThreshold": {
#       "operator": ">=",
#       "value": 1
#     },
#     "element": {
#       "elementId": "558e211f-2611-4010-85e4-fad4b9b435ca",
#       "name": "/platform/oauth/token",
#       "category": "REQUEST",
#       "userpath": "api_savedsearch",
#       "parent": "Obtain OAuth Token"
#     }
#   }
#

# https://github.com/kyrus/python-junit-xml
# https://github.com/kyrus/python-junit-xml/blob/master/junit_xml/__init__.py
def writeJUnitSLAContent(slas,test,filepath):

    logger = logging.getLogger("root")
    if slas is None: return

    logger.info("writeJUnitSLAContent: " + test.id + " to " + filepath)

    try:
        indicators = slas['indicators']
        perrun = slas['perrun']
        perinterval = slas['perinterval']

        suites = []

        for sla in perrun:
            ts = getSLATestSuites(test,"PerRun",sla)
            suites.append(ts)

        for sla in perinterval:
            ts = getSLATestSuites(test,"PerInterval",sla)
            suites.append(ts)

        logger.debug(TestSuite.to_xml_string(suites))

        with open(filepath, 'w') as f:
            TestSuite.to_file(f, suites, prettyprint=True)

        return True
    except:
        logger.error("Unexpected error at 'writeJUnitSLAContent':", sys.exc_info()[0])

    return False

def getSLATestSuites(test,group,sla):
    #pprint(vars(sla))

    slaprofile = sla.element.category#"SLANAME"
    userpath = "" if sla.element.userpath is None else sla.element.userpath
    suitename = "com.neotys." + slaprofile + "." + group + ("" if userpath == "" else "." + userpath)
    testname = sla.kpi
    tc = TestCase(testname,suitename)
    if sla.status == "PASSED":
        tc.stdout = ""#"Value is " + str(sla.value)
    elif sla.status == "FAILED":
        txt = getSLAJUnitText(test,group.lower(),sla,slaprofile,userpath)
        tc.add_error_info("SLA failed",txt,'NeoLoad SLA')
    elif sla.status == "WARNING":
        txt = getSLAJUnitText(test,group.lower(),sla,slaprofile,userpath)
        #tc.add_error_info("SLA failed",txt,'NeoLoad SLA')
    else:
        logging.warning("Unknown sla.status value: " + sla.status)

    return TestSuite(suitename,[tc])


def getSLAJUnitText(test,group,sla,slaprofile,userpath):

    slaType = "Per Run" if group == "perrun" else "Per Interval" if group == "perinterval" else "Unknown"
    opAndValue = ""
    if sla.failed_threshold is not None and sla.status == "FAILED":
        opAndValue = sla.failed_threshold.operator + " " + str(sla.failed_threshold.value)
    if sla.warning_threshold is not None and sla.status == "WARNING":
        opAndValue = sla.warning_threshold.operator + " " + str(sla.warning_threshold.value)

    reported = sla.value if group == "perrun" else sla.failed if sla.status == "FAILED" else sla.warning if sla.status == "WARNING" else 0

    txt = ("Container: " + sla.element.name + "\n"
            "Path: User Paths > " + userpath + " > Init > " + sla.element.parent + " > " + sla.element.name + "\n"
            "Virtual User: " + userpath + "\n"
            "SLA Profile: " + slaprofile + "\n"
            "SLA Type: " + slaType + "\n"
            "" + sla.status.title() + " Type: " + sla.kpi + "\n"
            "Project: " + test.project + "\n"
            "Scenario: " + test.scenario + "\n"
            "\n"
            "" + sla.status.title() + " description: " + "\n"
            "\n"
            "if the" + "\n"
            "	 " + sla.kpi + " " + opAndValue + "\n"
            "then" + "\n"
            "	 fail" + "\n"
            "\n"
            "Results: " + "\n"
            "\n"
            "" + sla.kpi + " = " + str(reported) + "%" + "\n"
            "\n"
            "Created N/A " + "\n") # maybe from test completion time?/?
    return txt

def getSLATextSummary(slas,test):

    logger = logging.getLogger("root")
    logger.info("getSLATextSummary: " + test.id)

    ret = ""

    if slas is not None:

        try:
            indicators = slas['indicators']
            perrun = slas['perrun']
            perinterval = slas['perinterval']

            for sla in perrun:
                thisText = getSingleLineSLAText(test,"PerRun",sla)
                ret += thisText + "\n"

            for sla in perinterval:
                thisText = getSingleLineSLAText(test,"PerInterval",sla)
                ret += thisText + "\n"

        except:
            logger.error("Unexpected error at 'writeJUnitSLAContent':", sys.exc_info()[0])
            ret = "SLA derivation process failed."

    return ret

def getSingleLineSLAText(test,type,sla):
    #ctext
    color = None if not isInteractiveMode() else "red" if sla.status == "FAILED" else "green" if sla.status == "PASSED" else "yellow"

    element = "{0} > {1} > {2}".format(
        sla.element.userpath,
        sla.element.parent,
        sla.element.name
    )

    whereFormat = "{0} [{1} {2}]"
    where = None
    if type == "PerInterval":
        if sla.status == "PASSED":
            where = None
        elif sla.status == "FAILED":
            where = whereFormat.format(sla.failed,sla.failed_threshold.operator,sla.failed_threshold.value)
        else:
            where = whereFormat.format(sla.warning,sla.warning_threshold.operator,sla.warning_threshold.value)

    return ctext(type + "SLA[{0}] {1} on [{2}]{3}".format(
        sla.kpi,
        sla.status,
        element,
        (" " + where) if where is not None else ""
    ),color)

# https://jenkins.io/blog/2016/07/01/html-publisher-plugin/
