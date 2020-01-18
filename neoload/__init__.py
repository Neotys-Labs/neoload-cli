
import six
from pyfiglet import figlet_format
from termcolor import colored
import logging
from PyInquirer import (prompt)
import importlib

colorPrint = True
interactiveMode = False
quietMode = False
offlineMode = False

def getDefaultLogger():
    return logging.getLogger("root")

def cprint(string, color=None, font="slant", figlet=False):
    if not isQuietMode():
        six.print_(ctext(string,color,font,figlet))

def ctext(string, color=None, font="slant", figlet=False):
    if colored and color is not None and colorPrint:
        if not figlet:
            return colored(string, color)
        else:
            return colored(figlet_format(string, font=font), color)
    else:
        return string


def cprintOrLogInfo(explicitPrint, logger, string, color=None, font="slant", figlet=False):
    if(explicitPrint):
        cprint(string,color,font,figlet)
    else:
        logger.info(string)


def dprompt(options):
    if isInteractiveMode():
        return prompt(options)
    else:
        logger = getDefaultLogger()
        logger.warning("Required input during non-interactive session used defaults.")

        allOptions = []
        if type(options) is list:
            allOptions.extend(options)
        elif type(options) is dict:
            allOptions.append(options)

        ret = {}
        for option in allOptions:
            ret[option['name']] = None if 'default' not in option else option['default']
        return ret

def setColorEnabled(enabled):
    global colorPrint
    colorPrint = enabled

def isLoggerInDebug(logger):
    return logger.getEffectiveLevel()==logging.DEBUG

def isInteractiveMode():
    return interactiveMode

def setInteractiveMode(enabled):
    global interactiveMode
    interactiveMode = enabled

def isQuietMode():
    return quietMode

def setQuietMode(quiet):
    global quietMode
    quietMode = quiet

def isOfflineMode():
    return offlineMode

def setOfflineMode(offline):
    global offlineMode
    offlineMode = offline

def pauseIfInteractiveDebug(logger,msgIfDebug=None):
    msg = "Debugging WAIT: press enter to continue...at your own risk" if msgIfDebug is None else msgIfDebug
    if isLoggerInDebug(logger) and isInteractiveMode():
        input(msg)
        return True

    return False

# used by openapi_client:runtime_api.post_upload_project...
# provides dynamic inspection/injection of servers defined in OpenAPI spec
def getCurrentFilesUrl():
    Profile_mod = importlib.import_module(".Profile",package="neoload")
    return Profile_mod.getProfileFilesUrl(Profile_mod.getCurrentProfile())
