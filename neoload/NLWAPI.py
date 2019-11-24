import logging
import openapi_client
from openapi_client.rest import ApiException

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
