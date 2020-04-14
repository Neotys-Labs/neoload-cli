import pytest
from utils import *

@pytest.mark.profiles
def test_profiles_empty():
    assertOutput(
        contains="No profiles",
        args="--profiles")
    #assert False, "Used to validate that a tee pipe retains exit PIPESTATUS in $?"

@pytest.mark.profiles
def test_profile_empty():
    assertOutput(
        contains="requires an argument",
        args="--profile")

@pytest.mark.profiles
def test_profile_create_wo_params():
    assertOutput(
        contains="specify all required profile elements",
        args="--profile test")

@pytest.mark.profiles
def test_profile_create_with_valid_zone_no_url():
    assertOutput(
        contains="specify all required profile elements",
        args="--profile test --zone 1234")

@pytest.mark.profiles
def test_profile_create_with_valid_url_no_zone():
    assertOutput(
        contains="specify all required profile elements",
        args="--profile test --url='http://fake/'")

@pytest.mark.profiles
def test_profile_create_with_nts_credentials():
    requireTestSecrets()
    assertProfileByZone(os.environ['NEOLOAD_CLI_ZONE_STATIC'])
    verifies = [
        'NEOLOAD_CLI_ZONE_STATIC',
        'NEOLOAD_CLI_NLW_URL',
        'NEOLOAD_CLI_NLW_TOKEN',
        'NEOLOAD_CLI_NTS_LOGIN',
        'NEOLOAD_CLI_NTS_URL',
    ]
    verifies = list(map(lambda x: os.environ[x],verifies))
    assertOutput(
        contains=verifies,
        printOutput=True,
        clearConfig=False,
        args={
            '--profile': 'test',
            '--summary': None,
        })

@pytest.mark.profiles
def test_profile_create_with_filesurl():
    requireTestSecrets()
    assertProfileByZone(os.environ['NEOLOAD_CLI_ZONE_STATIC'])
    verifies = [
        'NEOLOAD_CLI_ZONE_STATIC',
        'NEOLOAD_CLI_NLW_URL',
        'NEOLOAD_CLI_NLW_TOKEN',
        'NEOLOAD_CLI_NTS_LOGIN',
        'NEOLOAD_CLI_NTS_URL',
        'NEOLOAD_CLI_NLW_FILES_URL',
    ]
    verifies = list(map(lambda x: os.environ[x],verifies))
    assertOutput(
        contains=verifies,
        printOutput=True,
        clearConfig=False,
        args={
            '--profile': 'test',
            '--summary': None,
        })
