import pytest
from utils import *
from pytest_steps import test_steps, optional_step, depends_on
from os import path

@pytest.mark.slow
def test_attach_detatch_simple():
    requireTestSecrets()
    assertProfileByZone(os.environ['NEOLOAD_CLI_ZONE_STATIC'])
    assertNoDockerContainersRunning()
.
    assertOutput(
        contains="All containers are attached and ready for use",
        printOutput=True,
        clearConfig=False,
        args={
            '--attach': 'docker#3,neotys/neoload-loadgenerator:7.0.2'
        })
    assertOutput(
        contains="Removing network",
        printOutput=True,
        clearConfig=False,
        args={
            '--detatch': None
        })

@pytest.mark.slow
def test_attach_run_allinone():
    requireTestSecrets()
    assertProfileByZone(os.environ['NEOLOAD_CLI_ZONE_STATIC'])
    assertNoDockerContainersRunning()

    assertOutput(
        contains=[
            "All containers are attached and ready for use",
            "Project uploaded",
            "Test running",
            "Removing network",
        ],
        printOutput=True,
        clearConfig=False,
        args={
            '--debug': None,
            '-f '+ os.path.abspath("tests/example_pytests/default.yaml") : None,
            '--scenario': 'sanityScenario',
            '--attach': 'docker#1,neotys/neoload-loadgenerator:7.0.2'
        })

################################################################################
### Test Goal: verify that all steps in non-blocking execution work as expected
################################################################################
@pytest.mark.slow
@test_steps('prepare','attach', 'kickoff', 'getid', 'spinwait', 'detatch')
def test_attach_run_async():

    # Step: prepare
    requireTestSecrets()
    assertProfileByZone(os.environ['NEOLOAD_CLI_ZONE_STATIC'])
    assertNoDockerContainersRunning()
    yield

    # Step: attach
    assertOutput(
        contains=[
            "All containers are attached and ready for use",
        ],
        printOutput=True,
        clearConfig=False,
        args={
            '--attach': 'docker#1,neotys/neoload-loadgenerator:7.0.2'
        })
    yield

    # Step: kickoff
    outFile = os.path.abspath("async.stdout")
    assertOutput(
        contains=[
            "Project uploaded",
            "Test logs available at",
        ],
        printOutput=True,
        clearConfig=False,
        args={
            '--nowait': None,
            '--scenario': 'sanityScenario',
            '-f '+ os.path.abspath("tests/example_pytests/default.yaml") : None,
            '-f '+ os.path.abspath("tests/example_pytests/slas/uat.yaml") : None,
            '--outfile '+ outFile : None,
        })
    assert path.exists(outFile), "Could not find a test execution at: " + outFile
    yield

    # Step: getid
    testId = assertOutput(
        exitCode=0,
        printOutput=True,
        clearConfig=False,
        args={
            '--infile '+ outFile : None,
            '--query': 'testid'
        })
    assert (testId is not None and len(testId) > 0), "Could not obtain a proper bench ID."
    yield

    # Step: spinwait
    junitPath = os.path.abspath("junit_docker.xml")
    assertOutput(
        contains=[
            "Test running",
            "Test completed",
        ],
        printOutput=True,
        clearConfig=False,
        args={
            '--spinwait': None,
            '--summary': None,
            '--junitsla '+ junitPath : None,
            '--testid': testId
        })
    assert path.exists(junitPath), "Could not find a jUnit SLA report at: " + junitPath
    yield

    # Step: detatch
    assertOutput(
        contains=[
            "Removing network",
        ],
        printOutput=True,
        clearConfig=False,
        args={
            '--detatch': None,
        })
    yield
