import pytest
from utils import *

@pytest.mark.basic
def test_validate_version():
    assertOutput(
        contains=[
            "NeoLoad CLI version",
        ],
        exitCode=0,
        printOutput=True,
        clearConfig=False,
        args={
            '--version': None,
        })
