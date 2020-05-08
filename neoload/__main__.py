#!/usr/bin/env python3

import os
import platform
import sys
import shutil
import time
import logging
import re
import pkg_resources
import inspect

from neoload import *
from .Validators import *
from .Profile import *
from .Files import *
from .NLWAPI import *
from .Attaching import (attachInfra,detatchInfra,detatchAllInfra,isAlreadyAttached)
from .Formatting import printNiceTime
from .SimpleReports import writeJUnitSLAContent,getSLATextSummary
from openapi_client.rest import ApiException
from pprint import pprint
from contextlib import redirect_stdout
import datetime
from datetime import timedelta

import webbrowser
import click
import termcolor

trueValues = ['1','yes','true','on']
class ArgumentException(Exception):
    pass

API_VERSION = 20191115
CHECKZONESBEFORERUN = False
ALLOWZONELISTING = False

def initFeatureFlags(profile):
    if profile is None:
        return

    logger = getDefaultLogger()

    global API_VERSION, CHECKZONESBEFORERUN, ALLOWZONELISTING

    try:
        API_VERSION = getApiInternalVersionNumber(profile)
        logger.debug("profile[apiversion]: " + (profile["apiversion"] if 'apiversion' in profile else ''))
    except Exception as e:
        logger.error(e)

    # Zone capabilities support
    ZONES_SUPPORTED = (API_VERSION >= 20191215)
    CHECKZONESBEFORERUN = ZONES_SUPPORTED
    ALLOWZONELISTING = ZONES_SUPPORTED


# https://click.palletsprojects.com/en/7.x/options/

@click.command()
@click.option('--version', is_flag=True, default=None, help='Print the version of NeoLoad CLI')
@click.option('--profiles', is_flag=True, default=None, help='List profiles')
@click.option('--profile', default=None, help='Set profiles')
@click.option('--url', default=None, help='Set a url for selected profile')
@click.option('--token', default=None, help='Set a token for selected profile')
@click.option('--zone', default=None, help='Set a zone for selected profile')
@click.option('--ntslogin', default=None, help='Set the NTS login used for license acquisition')
@click.option('--ntsurl', default=None, help='Set the NTS URL used for license acquisition')
@click.option('--filesurl', default=None, help='Set the NLW API files url used for project file upload/download')
@click.option('--baseurl', default=None, help='Set the NLW front-end URL to be used for links and results references')
@click.option('files','--project','-f', multiple=True, help='Delimited list of project files, one or more, .nlp or YAML')
@click.option('--scenario', default=None, help='Run a specific scenario in provided project file(s)')
@click.option('--attach', default=None, help='Attaches containers for Controller and Load Generator(s)')
@click.option('--reattach', is_flag=True, help='Uses last --attach statement to create containers for Controller and Load Generator(s)')
@click.option('--detatch','-d', is_flag=True, help='Attempts to detatch and remove containers attached by this tool.')
@click.option('--detatchall','-da', is_flag=True, help='Detatches all local infrastructure instigated by this tool.')
@click.option('--retainresults', is_flag=True, default=None, help='Retain results in NeoLoad Web after test is completed.')
@click.option('--verbose', is_flag=True, default=None, help='Include INFO and WARNING detail.')
@click.option('--debug', is_flag=True, default=None, help='Include DEBUG, INFO and WARNING detail.')
@click.option('--nocolor', is_flag=True, default=None, help='Control color logs')
@click.option('--noninteractive','-ni', is_flag=True, default=False, help='Force processing as if console is non-interactive (i.e. not a user session)')
@click.option('--quiet', is_flag=True, default=False, help='Suppress non-critical console output.')
@click.option('--testid', default=None, help='Specify a Test ID (guid) for contextual operations such as reporting, modification, etc.')
@click.option('--testname', default=None, help='Specify a test name. Used when executing a test.')
@click.option('--testdesc', default=None, help='Specify a test description. Used when executing a test.')
@click.option('--query', default=None, help='Specifies a query (regex or jsonPath). Used in conjunction with --nowait and --outfile to derive testid and other details from after test is started.')
@click.option('--validate', is_flag=True, default=False, help='Runs validation passes only, does not start test.')
@click.option('--offline', is_flag=True, default=None, help='Run as if there is not an internet connection.')
@click.option('--summary', is_flag=True, default=None, help='Display a summary of the test.')
@click.option('--justid', is_flag=True, default=None, help='Output just the ID of the relevant artifact; infers --quiet flag')
@click.option('--outfile', default=None, help='Specify a file to also write all stdout to.')
@click.option('--infile', default=None, help='Specifies a file to run summary/query commands on. Used in conjunction with --nowait and --query to derive testid and other details from after test is started.')
@click.option('--junitsla', default=None, help='Path to write jUnit SLA report')
@click.option('--updatename', default=None, help='Updates the name of a test, incl. hashtag processing.')
@click.option('--updatedesc', default=None, help='Updates the description of a test, incl. hashtag processing.')
@click.option('--updatestatus', default=None, help='Updates the status of a test (PASSED|FAILED).')
@click.option('--rolltag', default=None, help='Adds the specified hashtag to the description of a test AND removes the tag from all prior executions of that test (by scenario and project name). Used in rolling baselines.')
@click.option('--delete', help='Deletes a resource; used with --profile --testid and other resource identifiers; prompts unless --quiet')
@click.option('--nowait', is_flag=True, default=None, help='Do not wait for blocking events, return immediately. To be used in conjunction with running a test.')
@click.option('--spinwait', is_flag=True, default=None, help='Block execution until a test is done or failure to connect to API. To be used in conjunction with --testid specifier.')
@click.option('--tests', is_flag=True, default=None, help='List tests')
@click.option('--zones', is_flag=True, default=None, help='List zones')
def main(   version,
            profiles,profile,url,token,zone,ntslogin,ntsurl,filesurl,baseurl,       # profile stuff
            files,scenario,attach,reattach,detatch,detatchall,retainresults,        # runtime inputs
            verbose,debug,nocolor,noninteractive,quiet,validate,offline,            # logging and debugging
            testid,testname,testdesc,query,                                                           # entities (primarily, a test)
            summary,justid,outfile,infile,junitsla,                                 # export operations
            updatename,updatedesc,updatestatus,rolltag,                             # modification ops (particularly, for a test)
            delete,
            nowait,spinwait,                                                        # support for non-blocking execution
            tests,zones
    ):

    setOfflineMode(offline)


    # collections of arguments for verification of combinations
    execops = [spinwait]
    exportops = [summary,justid,junitsla,query]
    modops = [updatename,updatedesc,updatestatus,rolltag,delete]
    infraops = [attach,reattach,detatch]
    listops = [tests,zones]
    # operations that can live on their own (like detatch, profiles, etc.)
    standaloneops = [detatch,profiles,version,zones]

    # in prep for argument combinatory validations
    allops = execops + exportops + modops + infraops + standaloneops + listops
    allids = [testid,profile,infile]


    #TODO: implement retainresults=False to delete results afterward (for sanity tests)

    if not isProfileInitialized(getCurrentProfile()) and version:
        printVersionNumber()
        return exitProcess(0)

    # initialize most rudimentary runtime indicators
    moreinfo = True if debug is not None or verbose is not None else False
    interactive = False if platform.system().lower() == 'linux' or noninteractive else True

    # indicate to this process if running as an interactive console (human) or CI
    setInteractiveMode(interactive)

    # if intent includes indicators to only output bare minimum output, set quiet flag
    if justid:
        quiet = True
    if infile is not None and query is not None:
        quiet = True
    setQuietMode(quiet)

    # configure logging options
    logger = configureLogging(debug,verbose,moreinfo,interactive,nocolor)
    if outfile:
        sys.stdout = Logger(outfile)

    # for headless, non-interactive systems, flush output immediately on all prints
    configurePythonUnbufferedMode(moreinfo)

    # initialize poor person's feature flags
    currentProfile = getCurrentProfile()
    if isProfileInitialized(currentProfile):
        initFeatureFlags(currentProfile)
    rememberedAPIVersion = currentProfile['apiversion'] if currentProfile is not None and 'apiversion' in currentProfile else None

    # critical flags for subsequent execution modes
    hasFiles = True if files is not None and len(files)>0 else False
    intentToRun = True if hasFiles and scenario is not None else False
    if validate: intentToRun = False

    # argSpec = inspect.getargvalues(inspect.currentframe())
    # print(argSpec)
    # paramsSpecified = list(filter(lambda x: (
    #     eval(x.name) is not None
    #     ) and not (
    #         x.default is not None and eval(x.name) == x.default
    #     ), main.params))
    # print(paramsSpecified)
    # print(any(list(filter(lambda x: x.name != "files", paramsSpecified))))
    # if not validate and (
    #     hasFiles and scenario is None and not (
    #          any(list(map(lambda x: x.name == "files", main.params)))
    #     )
    # ):
    #     validate = True

    if not intentToRun:
        cprint("NeoLoad CLI", color="green", figlet=True)

    if not configureProfiles(profiles,profile,url,token,zone,ntsurl,ntslogin,filesurl,baseurl):
        return exitProcess(0)# this is informational listing only, no need to execute anything else

    #TODO: implement --profile x --attach blahblah as a profile-update-only operation, no actual attach

    currentProfile = getCurrentProfile()
    currentProfile['apiversion'] = rememberedAPIVersion
    #initFeatureFlags(currentProfile)

    explicitAttach = True if attach is not None else False
    explicitDetatch = True if detatch or detatchall else False
    #alreadyAttached = False

    # if reattaching, but no prior attach saved in profile, error out
    if reattach and getProfileAttach(currentProfile) is None:
        return exitProcess(3, "Trying to reattach, but no prior attach stored in current profile.")


    # prep local infra attachment based on arguments, produce output state for later steps
    attachConfig = configureAttach(attach,intentToRun,currentProfile,reattach)

    attach = attachConfig['attach']
    if attachConfig['alreadyAttached']:
        attach = getProfileAttach(currentProfile)

    if attach is not None:
        logger.debug("Attach: " + attach)
    else:
        logger.debug("No attachment spec; defaulting to local")
        attach = 'local'
        attachConfig['shouldAttach'] = intentToRun # what about --attach?

    currentProfile = attachConfig['currentProfile']
    alreadyAttached = attachConfig['alreadyAttached']
    shouldAttach = attachConfig['shouldAttach']

    #TODO: if profile's zone has no resources available (i.e. if not attaching), fail here (TBD Jan 2020)


    # if looking for a summary of the profile specified as an argument
    if summary and profile is not None and currentProfile is not None:
        print(currentProfile) # legit use of print for raw output

    #TODO: need to add validation that, if to be run, minimum-viable params are specified (like Scenario)

    # if there are files specified, package for the API and prep variables
    zipfile = None
    asCodeFiles = []
    pack = None
    shouldUpload = False
    anyIsNLP = False
    validateNLP = False

    if hasFiles:
        pack = packageFiles(files,validate)
        if not pack["success"]:
            return exitProcess(4, pack["message"])

        anyIsNLP = pack["anyIsNLP"]

        validateNLP = validate and anyIsNLP

        if not validate or anyIsNLP:
            shouldUpload = True
            zipfile = pack["zipfile"]
            asCodeFiles = pack["asCodeFiles"]
            logger.debug("zipfile: " + zipfile)
            logger.debug("asCodeFiles: " + str(asCodeFiles))

    # status variables for forthcoming process
    infra = {
        "ready": True, # assume that zone has available resources, no API for validating this yet
        "provider": "", # assume that there are resources already attached/attachable
    }
    exitCode = 0

    noApiNeeded = (infile is not None and query is not None)
    if validate: noApiNeeded = True
    if version and not intentToRun: noApiNeeded = True
    if validateNLP: noApiNeeded = False

    try:
        client = None

        if intentToRun and not isProfileInitialized(currentProfile):
            return exitProcess(4,"No profiles are initialized.")

        if not noApiNeeded:
            client = getNLWAPI(currentProfile)

            # check API connectivity
            if not checkAPIConnectivity(client):
                return exitProcess(4)

        logger.debug("shouldAttach=" + str(shouldAttach))
        logger.debug("intentToRun=" + str(intentToRun))

        if shouldAttach:
            logger.info("Attaching resources.")
            infra = attachInfra(currentProfile,attach,explicitAttach)
            currentProfile = updateProfileInfra(infra)
        else:
            if intentToRun and CHECKZONESBEFORERUN:
                zoneId = currentProfile["zone"]
                currentZones = list(filter(lambda z: z.id == zoneId,getZones(client)))
                if len(currentZones) < 1:
                    return exitProcess(5, "Zone [" + zoneId + "] could not be found.")
                else:
                    currentZone = currentZones[0]

                    if currentZone.type != "DYNAMIC":
                        all_ctrl_count = len(currentZone.controllers)
                        active_ctrl_count = len(list(filter(lambda r: r.status=="AVAILABLE",currentZone.controllers)))
                        all_lgs_count = len(currentZone.loadgenerators)
                        active_lgs_count = len(list(filter(lambda r: r.status=="AVAILABLE",currentZone.loadgenerators)))
                        if not (active_ctrl_count > 0 and active_lgs_count > 0):
                            msg = "\n Zone [" + zoneId + "] has no available controller + load generator(s)."
                            if not ('lastattach' in currentProfile and currentProfile['lastattach'] is not None):
                                msg += "\n The current local profile [" + getCurrentProfileName() + "] does not have a 'lastattach' key."
                            if not ('lastinfra' in currentProfile and currentProfile['lastinfra'] is not None):
                                msg += "\n The current local profile [" + getCurrentProfileName() + "] does not have a 'lastinfra' key."
                            msg += "\n Did you forget to --attach some dynamic resources or specify a dynamic infrastructure zone?"
                            return exitProcess(5,msg)

        infraReady = infra["ready"]

        # if intentToRun:
        #
        #     # TODO: if explicitly argumented numOfLGs, ensure below or equal to
        #     # that defined considering zones should be interrogated for max

        if (intentToRun and infraReady) or shouldUpload:
            # upload the project to the NeoLoad Web Runtime in prep of test
            projectDef = None
            if zipfile is not None:
                cprint("Uploading project.", "yellow")
                projectDef = uploadProject(client,zipfile)
                cprint("Project uploaded", "green")


        if intentToRun:

            if infraReady:

                # if upload successful, kick off the test
                projectLaunched = None
                if projectDef is not None:
                    projectId = projectDef.project_id
                    projectName = projectDef.project_name
                    zone = currentProfile["zone"]
                    if not (testname is not None and len(testname.strip()) > 0): # can't be blank
                        testname = projectName + "_" + scenario
                    testdesc = "" if testdesc is None else testdesc
                    cprint("Launching new test '" + testname + "': " + testdesc, "yellow") #testable
                    try:
                        projectLaunched = runProject(client,projectId,asCodeFiles,scenario,zone,infra,testname,testdesc)
                        cprint("Test queued [" + time.ctime() + "], receiving initial telemetry.", "green")
                    except ApiException as err:
                        logger.critical("API error: {0}".format(err))

                # if test was kicked off successfully, process async or sync next steps
                if projectLaunched is not None:
                    time.sleep( 5 ) # wait for NLW test queued
                    launchedTestId = projectLaunched.test_id

                    if nowait:
                        exitCode = 0
                        logging.warning("Test queued for execution in --nowait mode.")
                        logsUrl = getTestLogsUrl(currentProfile,launchedTestId)
                        cprintOrLogInfo(True,logger,"Test logs available at: " + logsUrl)
                    else:
                        exitCode = blockingWaitForTestCompleted(currentProfile,client,launchedTestId,moreinfo,junitsla,quiet,justid)

                    printTestSummary(client, projectLaunched.test_id, justid, moreinfo, debug)

            #end infraReady
        else: # not intentToRun

            if not any(list(map(lambda x: x is not None, standaloneops))) and (
                    (
                        any(list(map(lambda x: x is not None, allops))) and all(list(map(lambda x: x is None, allids)))
                    ) or (
                        any(list(map(lambda x: x is not None, allids))) and all(list(map(lambda x: x is None, allops)))
                    )
                ):
                raise ArgumentException("Activity without context (i.e. --updatedesc but no --testid)")

            if version:
                printVersionNumber()

            if zones is not None:
                if not ALLOWZONELISTING:
                    return exitProcess(10,getIncompatibleVersionMessage("zone listing"))
                else:
                    allZones = list(filter(lambda z: z.id is not None,getZones(client)))
                    cprint("Number of zones: " + str(len(allZones)))
                    for z in allZones:
                        all_ctrl_count = len(z.controllers)
                        active_ctrl_count = len(list(filter(lambda r: r.status=="AVAILABLE",z.controllers)))
                        all_lgs_count = len(z.loadgenerators)
                        active_lgs_count = len(list(filter(lambda r: r.status=="AVAILABLE",z.loadgenerators)))
                        cprint(" - " + z.id + "\t[" + z.type + "]\tCTRLs: (" + str(active_ctrl_count) + "/" + str(all_ctrl_count) + ")\tLGs: (" + str(active_lgs_count) + "/" + str(all_lgs_count) + ")\t" + z.name)

            # if a named query and source is provided
            if infile is not None and query is not None:
                found = None
                if query.lower() == "testid":
                    guid = re.compile("(\{){0,1}[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}(\}){0,1}")
                    for i, line in enumerate(open(infile)):
                        for match in re.finditer(guid, line):
                            logger.debug("match: " + str(match.group()))
                            found = match.group()
                else:
                    return exitProcess(3, "Query value '" + query + "' not implemented!")

                if found is not None:
                    print(found) # legit use of print for raw output
                else:
                    logger.warning("Nothing in file [" + infile + "] matching query [" + query + "]")

            # if testid is provided, handle various reasons for querying a test id
            if testid is not None:

                test = getTestStatus(client,testid)
                printSummary = summary

                # if test execution-related operations are specified, do them
                if any(list(map(lambda x: x is not None, execops))):
                    logger.debug("Execution on a test...")

                    if spinwait is not None:
                        cprintOrLogInfo(True,logger,"Resuming a blocking --spinwait for test: " + testid)
                        exitCode = blockingWaitForTestCompleted(currentProfile,client,testid,moreinfo,junitsla,quiet,justid)

                # if test modification-related operations are specified, do them
                if any(list(map(lambda x: x is not None, modops))):
                    logger.debug("Operating on a test...")
                    tobe = {
                        'name': test.name,
                        'description': test.description,
                        'qualityStatus': test.quality_status
                    }

                    if rolltag is not None:
                        test = processRollTag(client,testid,rolltag)
                    else:
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

                # if test export-related operations are specified, do them
                if any(list(map(lambda x: x is not None, exportops))) or printSummary:
                    logger.debug("Exporting test details...")

                    if junitsla is not None:
                        slas = getSLAs(client,test)
                        writeSLAs(client,test,slas,junitsla)

                    if printSummary:
                        printTestSummary(client, testid, justid, moreinfo, debug)

        if validate:
            cprint("All validations passed.","green")

    # handle argument related issues with a different exit code than 0,1,2 (per NeoLoadCmd)
    except ArgumentException as e:
        exitCode = 3
        logger.error(e)
    # handle any other exception and print stack trace for diagnosis putposes
    except Exception as e:
        exitCode = 2
        logger.error("Unexpected error:", sys.exc_info()[0])

    # if resources were attached and not in async where they will be detatched manually afterwards
    shouldDetatch = detatch or (shouldAttach and intentToRun)

    # do detatchments if appropriate
    if nowait:
        logger.warning("Skipping all cleanup tasks in --nowait mode.")
        cleanupAfter(pack,shouldDetatch=False,explicit=False,infra=infra)
    else:
        detatchAndCleanup(detatch,intentToRun,infra,currentProfile,shouldDetatch,
                            alreadyAttached,explicitAttach,explicitDetatch,pack,detatchall)

    if moreinfo:
        logger.info("Exiting with code: " + str(exitCode))

    return exitProcess(exitCode)

def exitProcess(exitCode,msg=None):
    if exitCode != 0 and msg is not None:
        getDefaultLogger().error(msg)

    sys.exit(exitCode)

    return exitCode

def printVersionNumber():
    version = pkg_resources.require("neoload")[0].version
    cprint("NeoLoad CLI version " + str(version))

def configureLogging(debug,verbose,moreinfo,interactive,nocolor):
    loggingLevel = logging.ERROR

    if debug is not None:
        loggingLevel = logging.DEBUG
    elif verbose is not None:
        loggingLevel = logging.INFO
    else:
        loggingLevel = logging.ERROR

    logging.basicConfig(level=loggingLevel)
    logger = getDefaultLogger()
    logger.setLevel(loggingLevel)

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
        getDefaultLogger().addHandler(console)

    if debug is not None:
        if moreinfo: cprint("logging level set to DEBUG","red")
    elif verbose is not None:
        if moreinfo: cprint("logging level set to INFO","red")
    else:
        if moreinfo: cprint("logging level set to ERROR","red")

    return logger

def configurePythonUnbufferedMode(moreinfo):
    if moreinfo:
        unbuf = '' if os.getenv('PYTHONUNBUFFERED') is None else os.getenv('PYTHONUNBUFFERED')
        if unbuf.lower() in trueValues:
            getDefaultLogger().warning('Unbuffered output is on; CI jobs should report in real-time')
        else:
            getDefaultLogger().warning('Unbuffered output is off; CI jobs may delay output; set PYTHONUNBUFFERED=1')

def isProfileInitialized(profile):
    return (profile is not None and 'token' in profile and profile['token'] is not None and len(profile['token'].strip())>0)

def configureProfiles(profiles,profile,url,token,zone,ntsurl,ntslogin,filesurl,baseurl):
    if profiles is not None:
        listProfiles()
        return False
    else:
        if profile is not None and token is not None and zone is not None:
            createOrUpdateProfile(profile,url,token,zone)
        else:
            loadProfile(profile,url,token,zone)

        if url is not None:
            setUrl(url)
        if zone is not None:
            setZone(zone)
        if token is not None:
            setToken(token)
        if ntsurl is not None:
            setNTSURL(ntsurl)
        if ntslogin is not None:
            setNTSLogin(ntslogin)
        if filesurl is not None:
            setFilesUrl(filesurl)
        if baseurl is not None:
            setBaseUrl(baseurl)

    return True

def configureAttach(attach,intentToRun,currentProfile,reattach):
    ret = {}
    logger = getDefaultLogger()
    infra = getProfileInfra(currentProfile)
    alreadyAttached = isAlreadyAttached(infra)
    shouldAttach = False if attach is None else True
    if attach is not None:
        currentProfile = updateProfileAttach(attach)
    else:
        if intentToRun or reattach:
            if alreadyAttached:
                shouldAttach = False
                logger.warning("Reusing profile attach: " + str(infra))
                logger.debug("alreadyAttached: " + str(alreadyAttached))
            else:
                attach = getProfileAttach(currentProfile)
                if attach is not None:
                    shouldAttach = True
                    logger.warning("Prior infrastructure could not be revived; need to restart.")

    ret['currentProfile'] = currentProfile
    ret['alreadyAttached'] = alreadyAttached
    ret['shouldAttach'] = shouldAttach
    ret['attach'] = attach

    return ret

def printTestSummary(client,testId,justid,moreinfo,debug):
    if justid:
        print(test.id) # legit use of print for raw output
    else:
        test = getTestStatus(client,testId)

        printSLASummary(client,test)

        if moreinfo or debug:

            stats = None
            if test.status in ['STARTED','RUNNING','TERMINATED']:
                stats = getTestStatistics(client,testId)

            json = {
                'summary': test
            }
            if stats is not None:
                json['statistics'] = stats
            print(json) # legit use of print for raw output

def printSLASummary(client,test):
    cprint("SLA summary:")
    slas = getSLAs(client,test)
    text = getSLATextSummary(slas,test)
    cprint(text)

def blockingWaitForTestCompleted(currentProfile,client,launchedTestId,moreinfo,junitsla,quiet,justid):
    logger = getDefaultLogger()

    overviewUrl = getTestOverviewUrl(currentProfile,launchedTestId)
    logsUrl = getTestLogsUrl(currentProfile,launchedTestId)
    getDefaultLogger().info("Test logs available at: " + logsUrl)
    if moreinfo and isInteractiveMode():
        webbrowser.open_new_tab(logsUrl)
    test = None
    inited = False
    started = False
    running = False
    terminated = False
    waiterations = 0
    liveSummary = not quiet
    startedAt = datetime.datetime.now()
    waterator = '.'
    while not terminated:
        test = getTestStatus(client,launchedTestId)
        if test.status == "INIT":
            if not inited:
                inited = True
                cprint("Est. duration: " + printNiceTime(test.duration/1000) + ", LG count: " + str(test.lg_count), "yellow")
                print("Test is initializing", end="") # legit use of print for incremental/always output
            if not quiet:
                print(""+waterator, end="") # legit use of print for incremental/always output
            waiterations += 1
            sys.stdout.flush()
        elif test.status == "STARTING":
            inited = inited #dummy
        elif test.status == "STARTED":
            if not started:
                cprint("Test started.", "green")
                started = True
        elif test.status == "RUNNING":
            if not running:
                if not quiet:
                    print("") # end the ...s  # legit use of print for incremental/always output
                waiterations = 0
                running = True
                cprint("Test overview now available at: " + overviewUrl)
                startedAt = datetime.datetime.now()
                if not quiet:
                    print("Test running", end="") # legit use of print for incremental/always output
                if liveSummary:
                    print("") # legit use of print for incremental/always output
                if isInteractiveMode():
                    webbrowser.open_new_tab(overviewUrl)
            if liveSummary:
                if (waiterations % 3) == 0:
                    print(getCurrentTestSummaryLine(waiterations,startedAt,client,test)) # legit use of print for incremental/always output
            elif not quiet:
                print(""+waterator, end="") # legit use of print for incremental/always output
            waiterations += 1
            sys.stdout.flush()
        elif test.status == "TERMINATED":
            if not terminated:
                if not quiet:
                    print("") # end the ...s # legit use of print for incremental/always output
                handleTestTermination(client,test)
                terminated = True
        else:
            cprint("Unknown status encountered '" + test.status + "'.", "red")

        if test.status == "TERMINATED":
            outcome = getTestOutcome(client,test)
            slas = outcome["slas"]

            exitCode = outcome["exitCode"]
            logger.debug("exitCode[a]: " + str(exitCode))

            if test.quality_status == "FAILED" and test.termination_reason == "POLICY":
                if not quiet:
                    cprint("One or more SLAs failed.")

            afterTermination(client,test,slas,junitsla)

        time.sleep( 5 )

    logger.debug("exitCode[b]: " + str(exitCode))
    return exitCode

def afterTermination(client,test,slas,junitsla):
    if junitsla is not None:
        writeSLAs(client,test,slas,junitsla)

def writeSLAs(client,test,slas,filepath):
    #slas = getSLAs(client,test)
    writeJUnitSLAContent(slas,test,filepath)

def cleanupAfter(pack,shouldDetatch,explicit,infra):
    logger = getDefaultLogger()

    if shouldDetatch:
        if infra is None:
            getDefaultLogger().warning("No prior infrastructure to detatch.")
        else:
            detatchInfra(infra,explicit)

    zipfile = pack["zipfile"] if pack is not None and "zipfile" in pack else None
    deleteAfter = pack["deleteAfter"] if pack is not None and "deleteAfter" in pack else False
    if deleteAfter:
        if zipfile is not None:
            os.remove(zipfile)
    else:
        cprintOrLogInfo(False,logger,"Skipping file cleanup as deleteAfter != True")

def handleTestTermination(client,test): # dictionary from NLW API of final status
    outcome = getTestOutcome(client,test)
    color = "green" if outcome["exitCode"] == 0 else "yellow" if outcome["exitCode"] == 1 else "red"
    cprint(outcome["message"], color)
    return outcome

def getTestOutcome(client,test): # dictionary from NLW API of final status
    msg = "Unknown"
    exitCode = 2
    slas = getSLAs(client,test)
    slaFailureCount = slas["failureCount"]

    if test.termination_reason == "FAILED_TO_START":
        msg = "Test failed to start."
        exitCode = 2
    elif test.termination_reason == "CANCELLED":
        msg = "Test cancelled."
        exitCode = 2
    elif test.termination_reason == "POLICY":
        msg = "Test completed."
        exitCode = 0
    elif test.termination_reason == "VARIABLE":
        msg = "Test completed variably."
        exitCode = 0
    elif test.termination_reason == "MANUAL":
        msg = "Test was stopped manually."
        exitCode = 2
    elif test.termination_reason == "LG_AVAILABILITY":
        msg = "Test failed due to load generator availability."
        exitCode = 2
    elif test.termination_reason == "LICENSE":
        msg = "Test failed because of license."
        exitCode = 2
    elif test.termination_reason == "UNKNOWN":
        msg = "Test failed for an unknown reason. Check logs."
        exitCode = 2
    else:
        msg = "Unknown 'termination_reason' value: " + test.termination_reason
        exitCode = 2
        pprint(test)

    if exitCode == 0 and slaFailureCount > 0:
        msg += "One or more SLAs failed." # additive VERY important for test suite
        exitCode = 1

    outcome = {}
    outcome["exitCode"] = exitCode
    outcome["message"] = msg
    outcome["slas"] = slas

    return outcome

def detatchAndCleanup(detatch,intentToRun,infra,currentProfile,shouldDetatch,
            alreadyAttached,explicitAttach,explicitDetatch,pack,detatchall):
    logger = getDefaultLogger()

    if detatch and not intentToRun:
        logger.info("Loading prior infrastructure from current profile.")
        infra = getProfileInfra(currentProfile)
        logger.debug("infra[restored]: " + str(infra))

    if shouldDetatch:
        containerCount = 0
        if infra is not None:
            containerCount = len(infra['container_ids']) if 'container_ids' in infra else 0

        logger.info("containerCount: " + str(containerCount))
        if containerCount > 0:
            logger.warning("Detatching " + str(shouldDetatch) + " prior containers.")
        #else:
        #    cprintOrLogInfo(True,logger,"No containers to detatch!")

    if not shouldDetatch and intentToRun and alreadyAttached:
        logger.warning("Reminder: you just ran a test without detatching infrastructure. Make sure you clean up after yourself with the --detatch argument!")

    explicitEither = True if explicitAttach or explicitDetatch else False
    cleanupAfter(pack,shouldDetatch,explicitEither,infra)

    if detatchall:
        detatchAllInfra(explicitDetatch)

    if shouldDetatch or detatchall:
        currentProfile = updateProfileInfra(None)

def getCurrentTestSummaryLine(waiterations,startedAt,client,test):
    datetimeFormat = '%Y-%m-%d %H:%M:%S.%f'
    currentDT = datetime.datetime.now()
    diff = datetime.datetime.strptime(str(currentDT), datetimeFormat) - datetime.datetime.strptime(str(startedAt), datetimeFormat)
    prefix = "{0}: {1}\t".format(
        waiterations,
        str(diff)
    )
    ret = prefix
    test = getTestStatus(client,test.id)
    if test.status in ['STARTED','RUNNING','TERMINATED']:
        stats = getTestStatistics(client,test.id)
        ret = prefix + "{0},Fail[{4}],LGs[{1}]\tCNC/VUs:{5}\tBPS[{2}]\tRPS:{3}\tavg(ms):{6}".format(
            test.status,
            test.lg_count,
            str(round(stats.total_global_downloaded_bytes_per_second,3)),
            str(round(stats.total_request_count_per_second,3)),
            stats.total_global_count_failure,
            ("N/A" if stats.last_virtual_user_count is None else stats.last_virtual_user_count),
            stats.total_request_duration_average
        )
    else:
        ret = prefix + "Status[{0}]".format(
            test.status
        )

    return ret

def getIncompatibleVersionMessage(featureMessage=None):
    return "The version of the API you are connected to [" + str(API_VERSION) + "] does not support this function" + ("" if featureMessage is None else ": "+str(featureMessage))

class Logger(object):
    def __init__(self, filename=None):
        self.terminal = sys.stdout
        self.log = None
        if filename is not None:
            self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)
        if self.log is not None:
            self.log.write(message)

    def flush(self,**kwargs):
        try:
            for key, value in kwargs.items():
                print("{0} = {1}".format(key, value))

            self.terminal.flush()
            if self.log is not None:
                self.log.flush()
        except Exception as e:
            getDefaultLogger().error("Logger.flush error:", sys.exc_info()[0])

if __name__ == '__main__':
    main()
