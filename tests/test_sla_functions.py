import pytest
from utils import *
from pytest_steps import test_steps, optional_step, depends_on
from os import path

@pytest.mark.slas
def test_run_fail_slas():
    requireTestSecrets()
    assertProfileByZone(os.environ['NEOLOAD_CLI_ZONE_STATIC'])
    assertNoDockerContainersRunning()

    assertOutput(
        contains=[
            "Test completed",
            "One or more SLAs failed",
            "PerRunSLA[count] FAILED"
        ],
        exitCode=1,
        printOutput=True,
        clearConfig=False,
        args={
            '--debug': None,
            '-f '+ os.path.abspath("tests/example_pytests/default.yaml") : None,
            '-f '+ os.path.abspath("tests/example_pytests/slas/fail.yaml") : None,
            '--scenario': 'slaMinScenario',
            '--attach': 'docker#1,neotys/neoload-loadgenerator:7.0.2'
        })
