
import six
from pyfiglet import figlet_format
from termcolor import colored
import logging

colorPrint = True
interactiveMode = False

def cprint(string, color=None, font="slant", figlet=False):
    if colored and color is not None and colorPrint:
        if not figlet:
            six.print_(colored(string, color))
        else:
            six.print_(colored(figlet_format(
                string, font=font), color))
    else:
        six.print_(string)

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

def pauseIfInteractiveDebug(logger,msgIfDebug=None):
    msg = "Debugging WAIT: press enter to continue...at your own risk" if msgIfDebug is None else msgIfDebug
    if isLoggerInDebug(logger) and isInteractiveMode():
        input(msg)
        return True

    return False
