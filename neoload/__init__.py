
import six
from pyfiglet import figlet_format
from termcolor import colored

colorPrint = True

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
