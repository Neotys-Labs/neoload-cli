#!/usr/bin/env python3

import os
import platform
import sys
import shutil
import time
import logging

from neoload import *
from .Validators import *
from .Profile import *
from .Files import *
from .NLWAPI import *
from .Attaching import (attachInfra,detatchInfra,detatchAllInfra,isAlreadyAttached)
from .Formatting import printNiceTime
from .SimpleReports import writeJUnitSLAContent
from openapi_client.rest import ApiException
from pprint import pprint

import webbrowser
import click
import termcolor

trueValues = ['1','yes','true','on']
class ArgumentException(Exception):
    pass

@click.command()
@click.option('--profiles', is_flag=True, default=None, help='List profiles')
@click.option('--profile', default=None, help='Set profiles')
#@click.option('--deleteprofile', help='Deletes a profiles')
@click.option('--url', default=None, help='Set a url for selected profile')
@click.option('--token', default=None, help='Set a token for selected profile')
@click.option('--zone', default=None, help='Set a zone for selected profile')
@click.option('files','--project','-f', multiple=True, help='Delimited list of project files, one or more, .nlp or YAML')
@click.option('--scenario', default=None, help='Run a specific scenario in provided project file(s)')
@click.option('--attach', default=None, help='Attaches containers for Controller and Load Generator(s)')
@click.option('--detatch','-d', is_flag=True, help='Attempts to detatch and remove containers attached by this tool.')
@click.option('--detatchall','-da', is_flag=True, help='Detatches all local infrastructure instigated by this tool.')
@click.option('--verbose', is_flag=True, default=None, help='Include INFO and WARNING detail.')
@click.option('--debug', is_flag=True, default=None, help='Include DEBUG, INFO and WARNING detail.')
@click.option('--nocolor', is_flag=True, default=None, help='Control color logs')
@click.option('--noninteractive','-ni', is_flag=True, default=False, help='Force processing as if console is non-interactive (i.e. not a user session)')
@click.option('--quiet', is_flag=True, default=False, help='Suppress non-critical console output.')
@click.option('--testid', default=None, help='Specify a Test ID (guid) for contextual operations such as reporting, modification, etc.')
@click.option('--summary', is_flag=True, default=None, help='Display a summary of the test.')
@click.option('--junitsla', default=None, help='Path to write jUnit SLA report')
@click.option('--updatename', default=None, help='Updates the name of a test, incl. hashtag processing.')
@click.option('--updatedesc', default=None, help='Updates the description of a test, incl. hashtag processing.')
@click.option('--updatestatus', default=None, help='Updates the status of a test (PASSED|FAILED).')
def main(profiles,profile,url,token,zone,                                           # profile stuff
            files,scenario,attach,detatch,detatchall,                               # runtime inputs
            verbose,debug,nocolor,noninteractive,quiet,                             # logging and debugging
            testid,                                                                 # entities (primarily, a test)
            summary,junitsla,                                                       # export operations
            updatename,updatedesc,updatestatus):                                    # modification ops (particularly, for a test)

    loggingLevel = logging.ERROR

    if debug is not None:
        loggingLevel = logging.DEBUG
    elif verbose is not None:
        loggingLevel = logging.INFO
    else:
        loggingLevel = logging.ERROR

    logging.basicConfig(level=loggingLevel)
    logger = logging.getLogger("root")
    logger.setLevel(loggingLevel)

    moreinfo = True if debug is not None or verbose is not None else False

    interactive = False if platform.system().lower() == 'linux' or noninteractive else True
    setInteractiveMode(interactive)
    setQuietMode(quiet)

    if interactive and nocolor is None:
        coloredlogs = __import__('coloredlogs')
        coloredlogs.install(level=loggingLevel)
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

    # if debug is not None:
    #     cprint("logging.ERROR=" + str(logging.ERROR),"red")
    #     cprint("logging.INFO=" + str(logging.INFO),"red")
    #     cprint("logging.DEBUG=" + str(logging.DEBUG),"red")
    #     cprint("Logging is set to: " + str(logger.getEffectiveLevel()),"red")

    logger.info("Platform: " + platform.system())

    hasFiles = True if files is not None and len(files)>0 else False
    intentToRun = True if hasFiles or scenario is not None else False

    if not intentToRun:
        cprint("NeoLoad CLI", color="blue", figlet=True)

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

    shouldAttach = False if attach is None else True
    profile = getCurrentProfile()
    explicitAttach = True if attach is not None else False
    explicitDetatch = True if detatch or detatchall else False
    alreadyAttached = False
    if attach is not None:
        profile = updateProfileAttach(attach)
    else:
        if intentToRun:
            alreadyAttached = True if 'lastinfra' in profile and isAlreadyAttached(profile['lastinfra']) else False
            if alreadyAttached:
                shouldAttach = False
                logger.warning("Reusing profile attach: " + str(profile['lastinfra']))
                logger.debug("alreadyAttached: " + str(alreadyAttached))
            else:
                attach = getProfileAttach(profile)
                if attach is not None:
                    shouldAttach = True
                    logger.warning("Prior infrastructure could not be revived; need to restart.")


    if profile is not None and summary:
        print(profile)


    #TODO: need to add validation that, if to be run, minimum-viable params are specified (like Scenario)
    zipfile = None
    asCodeFiles = []
    if hasFiles:
        #validateFiles(files)
        logger.debug(files)
        pack = packageFiles(files)
        zipfile = pack["zipfile"]
        asCodeFiles = pack["asCodeFiles"]
        logger.info("Zip file created: "+zipfile)
        logger.info("As-code files: " + ",".join(asCodeFiles))

    infra = {
        "ready": True, # assume that zone has available resources, no API for validating this yet
        "provider": "", # assume that there are resources already attached/attachable
    }

    exitCode = 0

    #infra["ready"] = False #TODO: temp debug REMOVE ASAP

    try:
        client = getNLWAPI(profile)

        logger.debug("shouldAttach=" + str(shouldAttach))
        logger.debug("intentToRun=" + str(intentToRun))

        if shouldAttach:
            logger.info("Attaching resources.")
            infra = attachInfra(profile,attach,explicitAttach)
            profile = updateProfileInfra(infra)

        if intentToRun:

            #if explicitly argumented numOfLGs, ensure below or equal to that defined
            # considering dynamic zones should be interrogated for max

            if infra["ready"]:

                projectDef = None
                if zipfile is not None:
                    cprint("Uploading project.", "yellow")
                    projectDef = uploadProject(client,zipfile)
                    cprint("Project uploaded", "green")

                projectLaunched = None
                if projectDef is not None:
                    projectId = projectDef.project_id
                    projectName = projectDef.project_name
                    zone = profile["zone"]
                    testName = projectName + "_" + scenario
                    cprint("Launching new test '" + testName + "'.", "yellow")
                    try:
                        projectLaunched = runProject(client,projectId,asCodeFiles,scenario,zone,infra,testName)
                        cprint("Test queued [" + time.ctime() + "], receiving initial telemetry.", "green")
                    except ApiException as err:
                        logger.critical("API error: {0}".format(err))


                if projectLaunched is not None:
                    time.sleep( 10 )
                    launchedTestId = projectLaunched.test_id
                    overviewUrl = getTestOverviewUrl(profile,launchedTestId)
                    logsUrl = getTestLogsUrl(profile,launchedTestId)
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
                        test = getTestStatus(client,launchedTestId)
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

                            afterTermination(client,test,junitsla)

                        time.sleep( 5 )

            #end infraReady
        else: # not intentToRun

            exportops = [summary,junitsla]
            modops = [updatename,updatedesc,updatestatus]
            infraops = [attach,detatch]

            allops = exportops + modops + infraops
            allids = [testid,profile]

            if (
                any(list(map(lambda x: x is not None, allops))) and all(list(map(lambda x: x is None, allids)))
                ) or (
                any(list(map(lambda x: x is not None, allids))) and all(list(map(lambda x: x is None, allops)))
                ):
                    raise ArgumentException("Activity without context (i.e. --updatedesc but no --testid)")

            if testid is not None:

                test = getTestStatus(client,testid)
                printSummary = summary

                if any(list(map(lambda x: x is not None, modops))):
                    logger.debug("Operating on a test...")
                    tobe = {
                        'name': test.name,
                        'description': test.description,
                        'qualityStatus': test.quality_status
                    }

                    if updatename is not None:
                        tobe['name'] = processUpdateText(tobe['name'],updatename)

                    if updatedesc is not None:
                        tobe['description'] = processUpdateText(tobe['description'],updatedesc)

                    if updatestatus is not None:
                        if updatestatus not in ['PASSED','FAILED']:
                             raise ArgumentException("Invalid test status value provided for update. Must be 'PASSED' or 'FAILED',")
                        tobe['qualityStatus'] = updatestatus

                    test = updateTestDescription(client,testid,tobe)
                    printSummary = True

                if any(list(map(lambda x: x is not None, exportops))) or printSummary:
                    logger.debug("Exporting test details...")

                    if junitsla is not None:
                        writeSLAs(client,test,junitsla)

                    if printSummary:
                        print(test)
                        stats = getTestStatistics(client,testid)
                        print(stats)

    except ArgumentException as e:
        exitCode = 3
        logger.error(e)
    except Exception as e:
        exitCode = 2
        logger.error("Unexpected error:", sys.exc_info()[0])

    shouldDetatch = detatch or (shouldAttach and intentToRun)

    #print("shouldDetatch: " + str(shouldDetatch))
    #print("detatch: " + str(detatch))
    #print("infra[in-proc]: " + str(infra))


    if detatch and not intentToRun:
        logger.info("Loading prior infrastructure from current profile.")
        infra = getProfileInfra(profile)
        logger.debug("infra[restored]: " + str(infra))

    if shouldDetatch and infra is not None:
        containerCount = len(infra['container_ids']) if 'container_ids' in infra else 0
        print("containerCount: " + str(containerCount))
        if containerCount > 0:
            logger.warning("Detatching " + str(shouldDetatch) + " prior containers.")
        else:
            logger.warning("No containers to detatch!")

    if not shouldDetatch and intentToRun and alreadyAttached:
        logger.warning("Reminder: you just ran a test without detatching infrastructure. Make sure you clean up after yourself with the --detatch argument!")

    cleanupAfter(zipfile,shouldDetatch,explicitDetatch,infra)

    if shouldDetatch:
        profile = updateProfileInfra(None)

    if detatchall:
        detatchAllInfra(explicitDetatch)

    if moreinfo:
        logger.info("Exiting with code: " + str(exitCode))

    sys.exit(exitCode)

def afterTermination(client,test,junitsla):
    if junitsla is not None:
        writeSLAs(client,test,junitsla)

def writeSLAs(client,test,filepath):
    slas = getSLAs(client,test.id)
    writeJUnitSLAContent(slas,test,filepath)



def cleanupAfter(zipfile,shouldDetatch,explicitDetatch,infra):
    logger = logging.getLogger("root")

    if shouldDetatch:
        if infra is None:
            logger.warning("No prior infrastructure to detatch.")
        else:
            detatchInfra(infra,explicitDetatch)

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
