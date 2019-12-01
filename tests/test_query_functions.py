import pytest
from utils import *
from os import path

def test_query_outfile_for_bench():

    # Step: getid
    testId = assertOutput(
        exitCode=0,
        printOutput=True,
        args={
            '--infile '+ os.path.abspath("tests/example_pytests/async.stdout") : None,
            '--query': 'testid'
        })
    assert (testId is not None and len(testId) > 0), "Could not obtain a proper bench ID."
