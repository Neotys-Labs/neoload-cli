import pytest
from utils import *
from pytest_steps import test_steps, optional_step, depends_on
from os import path

@pytest.mark.files
def test_run_invalid_yaml():
    requireTestSecrets()
    assertProfileByZone(os.environ['NEOLOAD_CLI_ZONE_STATIC'])
    assertNoDockerContainersRunning()

    assertOutput(
        contains=[
            "is not valid YAML",
        ],
        exitCode=4,
        printOutput=True,
        clearConfig=False,
        args={
            '--debug': None,
            '-f '+ os.path.abspath("tests/example_pytests/invalid_yaml.yaml") : None,
            '--scenario': 'sanityScenario',
        })
