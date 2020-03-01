import pytest
from utils import *
from pytest_steps import test_steps, optional_step, depends_on
from os import path
from zipfile import ZipFile
import tempfile
import sys

@pytest.mark.files
def test_validate_valid_file():
    assertOutput(
        contains=[
            "All validations passed",
        ],
        exitCode=0,
        printOutput=True,
        clearConfig=False,
        args={
            '--validate': None,
            '-f '+ os.path.abspath("tests/example_pytests/default.yaml") : None,
        })

@pytest.mark.files
def test_invalidate_broken_yaml():
    assertOutput(
        contains=[
            "is not valid YAML",
        ],
        exitCode=4,
        printOutput=True,
        clearConfig=False,
        args={
            '--validate': None,
            '-f '+ os.path.abspath("tests/example_pytests/broken_yaml.yaml") : None,
        })

@pytest.mark.files
def test_nlp_file():
    requireTestSecrets()
    assertProfileByZone(os.environ['NEOLOAD_CLI_ZONE_STATIC'])

    zippath = os.path.abspath("tests/example_pytests/openstreetmaps_nlp.zip")
    tmpdir = tempfile.mkdtemp()
    with ZipFile(zippath, 'r') as zipObj:
        # Extract all the contents of zip file in different directory
        zipObj.extractall(tmpdir)

    assertOutput(
        contains=[
            "Project uploaded",
            "All validations passed",
        ],
        exitCode=0,
        printOutput=True,
        clearConfig=False,
        args={
            '--scenario': 'sanityScenario',
            '-f '+ tmpdir + os.path.sep + "CLI_app_test.nlp" : None,
            '--validate': None,
        })

    try:
        os.remove(tmpzip) # get rid of temp file without extension
    except Exception as err:
        print("Could not remove temp directory '" + tmpdir + "' in 'test_nlp_file':", sys.exc_info()[0])
