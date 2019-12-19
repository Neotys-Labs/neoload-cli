import os
import pytest
from pyconfigstore3 import ConfigStore
import re
import subprocess

PYCONFIGSTORE_NAME_OVERRIDE = "neoload-cli-test"

def assertOutput(args,exitCode=None,contains=None,printOutput=False,clearConfig=True):

    argsStr = ""
    if type(args) is not None:
        if type(args) is str:
            argsStr = args
        elif type(args) is list:
            argsStr = " ".join(args)
        elif type(args) is dict:
            for key in args:
                argsStr += " " + key + ''
                if args[key] is not None:
                    argsStr += '=' + str(args[key]) + ''

    command = "neoload -ni " + argsStr.strip()

    print("Full Command: " + command)

    my_env = os.environ.copy()
    my_env["PYCONFIGSTORE_NAME_OVERRIDE"] = PYCONFIGSTORE_NAME_OVERRIDE

    if clearConfig:
        conf = ConfigStore(PYCONFIGSTORE_NAME_OVERRIDE)
        conf.clear()


    result = subprocess.run([command], shell=True, check=False, capture_output=True, universal_newlines=True, env=my_env)
    output = ""
    if result.stdout is not None:
        output += result.stdout
    if result.stderr is not None:
        output += result.stderr
    if printOutput:
        print('exitCode: ' + str(result.returncode))
        print(output)

    if contains is not None:
        allContains = []
        if type(contains) is str:
            allContains.append(contains)
        elif type(contains) is list:
            allContains.extend(contains)
        for find in allContains:
            index = output.lower().find(find.lower())
            assert index >= 0, "Could not find '" + find + "' in stdout:\n\n" + output

    if exitCode is not None:
        assert result.returncode == exitCode, "Process return code was not " + str(exitCode) + "."

    return output
# https://stackoverflow.com/questions/51736864/how-to-test-command-line-applications-in-python

NEOLOAD_CLI_NTS_LOGIN = 'NEOLOAD_CLI_NTS_LOGIN'
NEOLOAD_CLI_NTS_URL = 'NEOLOAD_CLI_NTS_URL'
NEOLOAD_CLI_NLW_TOKEN = 'NEOLOAD_CLI_NLW_TOKEN'
NEOLOAD_CLI_NLW_URL = 'NEOLOAD_CLI_NLW_URL'
NEOLOAD_CLI_ZONE_DYNAMIC = 'NEOLOAD_CLI_ZONE_DYNAMIC'
NEOLOAD_CLI_ZONE_STATIC = 'NEOLOAD_CLI_ZONE_STATIC'

def requireTestSecrets():

    required = [
        NEOLOAD_CLI_NTS_LOGIN,
        NEOLOAD_CLI_NTS_URL,
        NEOLOAD_CLI_NLW_TOKEN,
        NEOLOAD_CLI_NLW_URL,
        NEOLOAD_CLI_ZONE_DYNAMIC,
        NEOLOAD_CLI_ZONE_STATIC,
    ]

    for key in required:
        if key not in os.environ:
            raise Exception('Could not find an environment variable required for this test: ' + key)

def assertProfileByZone(zone):
    assertOutput(
        contains="Created profile: test",
        printOutput=True,
        clearConfig=True,
        args={
            '--profile': 'test',
            '--zone': zone,
            '--url': '$NEOLOAD_CLI_NLW_URL',
            '--token': '$NEOLOAD_CLI_NLW_TOKEN',
            '--ntslogin': '$NEOLOAD_CLI_NTS_LOGIN',
            '--ntsurl': '$NEOLOAD_CLI_NTS_URL',
        })

def assertNoDockerContainersRunning():
    assertOutput(
        contains="0 docker artifacts",
        printOutput=True,
        clearConfig=False,
        args={
            '--detatchall': None,
        })
