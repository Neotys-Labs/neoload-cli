import pytest
from utils import *

# def test_attach_detatch_simple():
#     requireTestSecrets()
#     assertProfileByZone(os.environ['NEOLOAD_CLI_ZONE_STATIC'])
#     assertOutput(
#         contains="All containers are attached and ready for use",
#         printOutput=True,
#         clearConfig=False,
#         args={
#             '--attach': 'docker#3,neotys/neoload-loadgenerator:7.0.2'
#         })
#     assertOutput(
#         contains="Removing network",
#         printOutput=True,
#         clearConfig=False,
#         args={
#             '--detatch': None
#         })

def test_attach_run_allinone():
    requireTestSecrets()
    assertProfileByZone(os.environ['NEOLOAD_CLI_ZONE_STATIC'])
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
            '-f '+ os.path.abspath("tests/example_2_0_runtime/default.yaml") : None,
            '--scenario': 'sanityScenario',
            '--attach': 'docker#1,neotys/neoload-loadgenerator:7.0.2'
        })


# def f():
#     raise SystemExit(1)
#
# def test_all():
#     with pytest.raises(SystemExit):
#         f()
