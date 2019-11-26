#!/usr/bin/env python3

import os
import platform
import sys
import shutil
import time
import logging

from neoload import *
from .Validators import *
from .Profile import (loadProfile,setZone,listProfiles,setToken,getCurrentProfile,createOrUpdateProfile)
from .Files import *
from .NLWAPI import (getNLWAPI,uploadProject,runProject,getTestStatus,getTestOverviewUrl,getTestLogsUrl)
from .Attaching import (attachInfra,detatchInfra)
from .Formatting import printNiceTime
from openapi_client.rest import ApiException
from pprint import pprint

import webbrowser
import click
import termcolor

trueValues = ['1','yes','true','on']

@click.command()
@click.option('-ps','--profiles', is_flag=True, default=None, help='List profiles')
@click.option('--profile', default=None, help='Set profiles')
#@click.option('--deleteprofile', help='Deletes a profiles')
@click.option('--url', default=None, help='Set a url for selected profile')
@click.option('--token', default=None, help='Set a token for selected profile')
@click.option('--zone', default=None, help='Set a zone for selected profile')
@click.option('files','--project','-f', multiple=True, help='Delimited list of project files, one or more, .nlp or YAML')
@click.option('--scenario', default=None, help='Run a specific scenario in provided project file(s)')
@click.option('--attach', default=None, help='Attaches containers for Controller and Load Generator(s)')
@click.option('--verbose', is_flag=True, default=None, help='Include INFO and WARNING detail.')
@click.option('--debug', is_flag=True, default=None, help='Include DEBUG, INFO and WARNING detail.')
@click.option('--nocolor', is_flag=True, default=None, help='Control color logs')
def main(profiles,profile,url,token,zone,files,scenario,attach,verbose,debug,nocolor):

    logger = logging.getLogger("root")

    if debug is not None:
        logger.setLevel(logging.DEBUG)
    elif verbose is not None:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)

    moreinfo = True if debug is not None or verbose is not None else False

    interactive = False if platform.system().lower() == 'linux' else True
    setInteractiveMode(interactive)

    if interactive and nocolor is None:
        coloredlogs = __import__('coloredlogs')
        coloredlogs.install()
    else:
        setColorEnabled(False)
        cprint("Color logs are disabled")

    if not interactive:
        # define a Handler which writes INFO messages or higher to the sys.stderr
        console = logging.StreamHandler()
        console.setLevel(logger.getEffectiveLevel())
        # add the handler to the root logger
        logging.getLogger('root').addHandler(console)


    if debug is not None:
        if moreinfo: cprint("logging level set to DEBUG","red")
    elif verbose is not None:
        if moreinfo: cprint("logging level set to INFO","red")
    else:
        if moreinfo: cprint("logging level set to ERROR","red")

    if moreinfo:
        unbuf = '' if os.getenv('PYTHONUNBUFFERED') is None else os.getenv('PYTHONUNBUFFERED')
        if unbuf.lower() in trueValues:
            logger.warning('Unbuffered output is on; CI jobs should report in real-time')
        else:
            logger.warning('Unbuffered output is off; CI jobs may delay output; set PYTHONUNBUFFERED=1')

    if debug is not None:
        cprint("logging.ERROR=" + str(logging.ERROR),"red")
        cprint("logging.INFO=" + str(logging.INFO),"red")
        cprint("logging.DEBUG=" + str(logging.DEBUG),"red")
        cprint("Logging is set to: " + str(logger.getEffectiveLevel()),"red")

    logger.info("This is an informational message.")

    logger.warning("Platform: " + platform.system())

    intentToRun = True if files is not None or scenario is not None else False

    if not intentToRun:
        cprint("NeoLoad CLI", color="blue")

    cprint("Welcome to NeoLoad CLI", "green")

    if profiles is not None:
        listProfiles()
        return
    else:
        if profile is not None and token is not None and zone is not None:
            createOrUpdateProfile(profile,url,token,zone)
        else:
            loadProfile(profile)

            if zone is not None:
                setZone(zone)

            if token is not None:
                setToken(token)

    #TODO: need to add validation that, if to be run, minimum-viable params are specified (like Scenario)
    zipfile = None
    asCodeFiles = []
    if files is not None and len(files)>0:
        #validateFiles(files)
        logger.debug(files)
        pack = packageFiles(files)
        zipfile = pack["zipfile"]
        asCodeFiles = pack["asCodeFiles"]
        logger.info("Zip file created: "+zipfile)
        logger.info("As-code files: " + ",".join(asCodeFiles))

    profile = getCurrentProfile()

    infra = {
        "ready": True, # assume that zone has available resources, no API for validating this yet
        "provider": "", # assume that there are resources already attached/attachable
    }

    cleanedUp = False
    exitCode = 0

    #infra["ready"] = False #TODO: temp debug REMOVE ASAP

    try:
        api = getNLWAPI(profile)

        if attach is not None:
            logger.info("Attaching resources.")
            infra = attachInfra(profile,attach)

        #if explicitly argumented numOfLGs, ensure below or equal to that defined
        # considering dynamic zones should be interrogated for max

        if infra["ready"]:

            projectDef = None
            if zipfile is not None:
                cprint("Uploading project.", "yellow")
                projectDef = uploadProject(api,zipfile)
                cprint("Project uploaded", "green")

            projectLaunched = None
            if projectDef is not None:
                projectId = projectDef.project_id
                projectName = projectDef.project_name
                zone = profile["zone"]
                testName = projectName + "_" + scenario
                cprint("Launching new test '" + testName + "'.", "yellow")
                try:
                    projectLaunched = runProject(api,projectId,asCodeFiles,scenario,zone,infra,testName)
                    cprint("Test queued [" + time.ctime() + "], receiving initial telemetry.", "green")
                except ApiException as err:
                    logger.critical("API error: {0}".format(err))


            if projectLaunched is not None:
                time.sleep( 10 )
                testId = projectLaunched.test_id
                overviewUrl = getTestOverviewUrl(profile,testId)
                logsUrl = getTestLogsUrl(profile,testId)
                logger.info("Test logs available at: " + logsUrl)
                if moreinfo:
                    webbrowser.open_new_tab(logsUrl)
                test = None
                inited = False
                started = False
                running = False
                terminated = False
                waiterations = 0
                while not terminated:
                    test = getTestStatus(api,testId)
                    if test.status == "INIT":
                        if not inited:
                            inited = True
                            cprint("Test is initializing...", "yellow")
                            cprint("Est. duration: " + printNiceTime(test.duration/1000) + ", LG count: " + str(test.lg_count), "yellow")
                    elif test.status == "STARTING":
                        inited = inited #dummy
                    elif test.status == "STARTED":
                        if not started:
                            cprint("Test started.", "green")
                            started = True
                    elif test.status == "RUNNING":
                        if not running:
                            running = True
                            cprint("Test overview now available at: " + overviewUrl)
                            print("Test running", end="")
                            webbrowser.open_new_tab(overviewUrl)
                        waiterations += 1
                        waterator = '.' #*waiterations
                        print(""+waterator, end="")
                        sys.stdout.flush()
                        #pprint("Test running"+ waterator +"\r")
                    elif test.status == "TERMINATED":
                        if not terminated:
                            print("") # end the ...s
                            handleTestTermination(test)
                            terminated = True
                    else:
                        cprint("Unknown status encountered '" + test.status + "'.", "red")

                    if test.status == "TERMINATED":
                        if test.quality_status == "PASSED":
                            exitCode = 0
                        else:
                            exitCode = 1

                    time.sleep( 5 )

        #end infraReady
    except:
        exitCode = 2
        logger.error("Unexpected error:", sys.exc_info()[0])

        cleanupAfter(zipfile,attach,infra)
        cleanedUp = True

        raise

    if not cleanedUp:
        cleanupAfter(zipfile,attach,infra)

    if moreinfo:
        logger.info("Exiting with code: " + str(exitCode))

    sys.exit(exitCode)


def cleanupAfter(zipfile,attach,infra):
    if attach is not None:
        detatchInfra(infra)

    if zipfile is not None:
        os.remove(zipfile)

def handleTestTermination(test): # dictionary from NLW API of final status
    if test.termination_reason == "FAILED_TO_START":
        cprint("Test failed to start.", "red")
    elif test.termination_reason == "POLICY":
        cprint("Test completed.", "green")
    elif test.termination_reason == "VARIABLE":
        cprint("Test completed variably.", "green")
    elif test.termination_reason == "MANUAL":
        cprint("Test was stopped manually.", "yellow")
    elif test.termination_reason == "LG_AVAILABILITY":
        cprint("Test failed due to load generator availability.", "red")
    elif test.termination_reason == "LICENSE":
        cprint("Test failed because of license.", "red")
    elif test.termination_reason == "UNKNOWN":
        cprint("Test failed for an unknown reason. Check logs.", "red")
    else:
        cprint("Unknown 'termination_reason' value: " + test.termination_reason, "red")
        pprint(test)

if __name__ == '__main__':
    main()
