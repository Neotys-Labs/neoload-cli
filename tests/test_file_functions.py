import pytest
from utils import *
from pytest_steps import test_steps, optional_step, depends_on
from os import path

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

@pytest.mark.schema
def test_invalidate_empty_file():
    assertOutput(
        contains=[
            "does not have enough properties",
        ],
        exitCode=4,
        printOutput=True,
        clearConfig=False,
        args={
            '--validate': None,
            '-f '+ os.path.abspath("tests/example_pytests/empty.yml") : None,
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

@pytest.mark.schema
def test_invalidate_invalid_to_schema_yaml():
    assertOutput(
        contains=[
            "Additional properties are not allowed",
        ],
        exitCode=4,
        printOutput=True,
        clearConfig=False,
        args={
            '--validate': None,
            '-f '+ os.path.abspath("tests/example_pytests/invalid_to_schema.yaml") : None,
        })

@pytest.mark.schema
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
            '-f '+ os.path.abspath("tests/example_pytests/everything.yaml") : None,
        })
