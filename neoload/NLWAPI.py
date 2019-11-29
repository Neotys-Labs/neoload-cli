import logging
import sys
import openapi_client
from openapi_client.rest import ApiException
from openapi_client.models import *

configuration = openapi_client.Configuration()

app = None

### to regenerate the API client
#   brew install openapi-generator
#   openapi-generator generate -i https://neoload-api.saas.neotys.com/explore/swagger.yaml -g python -o ~/git/temp/


def getNLWAPI(profile):
    url = profile["url"]
    if not url.endswith("/"): url = url + "/"
    url = url + "explore/swagger.yaml"

    token = profile["token"]

    #configuration.host = "http://petstore.swagger.io:80/v2"
    configuration.api_key['accountToken'] = token

    client = openapi_client.ApiClient(configuration)

    return client

def uploadProject(client,zipfile):
    api = openapi_client.RuntimeApi(client)
    resp = api.post_upload_project(file=zipfile)
    return resp

def runProject(client,projectId,asCodeFiles,scenario,zone,infra,testName):
    logger = logging.getLogger("root")
    api = openapi_client.RuntimeApi(client)
    asCodeLine = ",".join(asCodeFiles)#"default.yaml" + "," + ",".join(asCodeFiles)
    logger.debug(asCodeLine)

    lgCount = 1
    if "numOfLGs" in infra:
        lgCount = infra["numOfLGs"]

    resp = api.get_tests_run(
        name=testName,
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
    baseUrl="https://neoload.saas.neotys.com/#!result/"
    if 'baseurl' in profile:
        baseUrl=profile['baseurl']
    return baseUrl+testId

def getTestOverviewUrl(profile,testId):
    return getTestBaseUri(profile,testId)+'/overview'

def getTestLogsUrl(profile,testId):
    return getTestBaseUri(profile,testId)+'/logs'

def getSLAs(client,testId):
    logger = logging.getLogger("root")
    api = openapi_client.ResultsApi(client)
    try:
        return {
            'indicators': api.get_test_sla_global_indicators(testId),
            'perrun': api.get_test_sla_per_test(testId),
            'perinterval': api.get_test_sla_per_interval(testId),
        }
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
