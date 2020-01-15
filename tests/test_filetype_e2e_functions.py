import pytest
from utils import *
from os import path

################################################################################
### Test Goal: verify that zip file is parsable and produces expected results
################################################################################
@pytest.mark.slow
def test_verify_zip_file_type():
    requireTestSecrets()
    assertProfileByZone(os.environ['NEOLOAD_CLI_ZONE_STATIC'])
    assertNoDockerContainersRunning()

    assertOutput(
        contains=[
            "Project uploaded",
            "Test running",
            "Test completed"
        ],
        printOutput=True,
        clearConfig=False,
        args={
            '--debug': None,
            '-f '+ os.path.abspath("tests/example_2_0_runtime/Archive.zip") : None,
            '--scenario': 'sanityScenario',
            '--attach': 'docker#1,neotys/neoload-loadgenerator:7.0.2'
        })
