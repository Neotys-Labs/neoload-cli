from neoload import *

import logging
import sys
import openapi_client
from .Profile import (getCurrentProfile,getProfileFilesUrl)
from openapi_client.rest import ApiException
from openapi_client.models import *

app = None

### to regenerate the API client
#   brew install openapi-generator
#   openapi-generator generate -i https://neoload-api.saas.neotys.com/explore/swagger.yaml -g python -o ~/git/temp/


def getNLWAPI(profile):
    logger = logging.getLogger("root")

    url = profile["url"]
    if not url.endswith("/"): url = url + "/"
    url = url + "v1"

    token = profile["token"]

    logger.info("Using API URL: " + url)
    logger.info("Using API token: " + token)

    configuration = openapi_client.Configuration()

    configuration.host = url
    configuration.api_key['accountToken'] = token
    configuration.debug = isLoggerInDebug(logger)

    client = openapi_client.ApiClient(configuration)

    return client

def uploadProject(client,zipfile):
    api = openapi_client.RuntimeApi(client)
    resp = api.post_upload_project(file=zipfile)
    return resp

def runProject(client,projectId,asCodeFiles,scenario,zone,infra,testName,testDesc):
    logger = logging.getLogger("root")
    api = openapi_client.RuntimeApi(client)
    asCodeLine = ",".join(asCodeFiles)#"default.yaml" + "," + ",".join(asCodeFiles)
    logger.debug(asCodeLine)

    lgCount = 1
    if "numOfLGs" in infra:
        lgCount = infra["numOfLGs"]

    resp = api.get_tests_run(
        name=testName,
        description=testDesc,
        project_id=projectId,
        scenario_name=scenario,
        as_code=asCodeLine,
        controller_zone_id=zone,
        lg_zones=""+zone+":"+str(lgCount),
        )
    return resp

def getTestStatus(client,testId):
    api = openapi_client.ResultsApi(client)
    resp = api.get_test(testId)
    return resp

def getTestBaseUri(profile,testId):
    baseUrl="https://neoload.saas.neotys.com/"
    if 'baseurl' in profile:
        baseUrl=profile['baseurl']
    if not baseUrl.lower().endswith('/#!result/'):
        baseUrl = baseUrl + '/#!result/'
    baseUrl = baseUrl.replace("//","/")
    return baseUrl+testId

def getTestOverviewUrl(profile,testId):
    return getTestBaseUri(profile,testId)+'/overview'

def getTestLogsUrl(profile,testId):
    return getTestBaseUri(profile,testId)+'/logs'

def getSLAs(client,test):
    logger = logging.getLogger("root")
    api = openapi_client.ResultsApi(client)
    try:
        res = {
            'indicators': [] if test.status != "TERMINATED" else api.get_test_sla_global_indicators(test.id),
            'perrun': [] if test.status != "TERMINATED" else api.get_test_sla_per_test(test.id),
            'perinterval': api.get_test_sla_per_interval(test.id),
        }
        res["failureCount"] = (
            len(list(filter(lambda x: x.status == "FAILED", res["indicators"]))) +
            len(list(filter(lambda x: x.status == "FAILED", res["perrun"]))) +
            len(list(filter(lambda x: x.status == "FAILED", res["perinterval"])))
        )
        return res
    except:
        logger.error("Unexpected error at 'getSLAs:", sys.exc_info()[0])
        return None

def processUpdateText(l_original,l_updatespec):
    original  = "" if l_original is None else l_original
    updatespec = "" if l_updatespec is None else l_updatespec

    if updatespec.startswith("+"):
        return original + updatespec.replace("+","",1)
    elif updatespec.startswith("-"):
        return original.replace(updatespec.replace("-","",1),"")
    else:
        return updatespec

def updateTestDescription(client,testId,data):
    api = openapi_client.ResultsApi(client)
    upd = TestUpdateRequest(
        name=data["name"],
        description=data["description"],
        quality_status=data["qualityStatus"]
    )
    return api.update_test(testId,upd)

def getTestStatistics(client,testId):
    api = openapi_client.ResultsApi(client)
    return api.get_test_statistics(testId)

def processRollTag(client,testId,rolltag):
    logger = logging.getLogger("root")
    api = openapi_client.ResultsApi(client)

    test = getTestStatus(client,testId)

    # get a clean version of the tag text, no modifiers
    newTag = rolltag.replace("+","").replace("-","").replace("#","")

    # list all prior tests matching project and scenario name
    priors = api.get_tests(project=test.project,status="TERMINATED",limit=200,offset=0)
    tagged = list(filter(lambda prior: prior.scenario == test.scenario and ("#"+newTag) in (prior.description+""), priors))
    for prior in tagged:
        logger.info("Removing tag [" + newTag + "] from test [" + prior.id + "].")
        nowPrior = changeTestTag(client,prior.id,newTag,True)

    logger.info("Adding tag [" + newTag + "] to test [" + prior.id + "].")
    return changeTestTag(client,testId,newTag,True)


def changeTestTag(client,testId,tagraw,isAdd):
    logger = logging.getLogger("root")
    api = openapi_client.ResultsApi(client)

    test = getTestStatus(client,testId)
    tag = (tagraw).replace("+","").replace("-","").replace("#","")
    oldDesc = (test.description+"").replace("#"+tag,"")
    spec = ("+" if isAdd else "-") + "#" + tag
    upd = TestUpdateRequest(
        name=test.name,
        description=processUpdateText(oldDesc,spec),
        quality_status=test.quality_status
    )
    return api.update_test(testId,upd)

def getZones(client):
    api = openapi_client.ResourcesApi(client)

    return api.get_zones()

def checkAPIConnectivity(client):
    logger = logging.getLogger("root")
    api = openapi_client.ResultsApi(client)
    try:
        tests = api.get_tests(limit=1,offset=0)
        return True
    except:
        logger.error("Unexpected error at 'checkAPIConnectivity:", sys.exc_info()[0])
        return False
