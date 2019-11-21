
from neoload import *

from .Validators import *
from pyconfigstore3 import ConfigStore
from PyInquirer import (prompt)

import json
import logging

profileprefix = "profile_"

conf = ConfigStore("neoload-cli")

def getNLWURL():
    proname = getCurrentProfileName()
    if proname is None:
        proname = getDefaultProfileName()
    profile = getProfileByName(proname)
    return None if profile is None else profile.get("url")


def getNLWSaaSAPIURL():
    return "https://neoload-rest.saas.neotys.com"

def askNLWAPI():
    questions = [
        {
            'type': 'input',
            'name': 'token',
            'message': 'Enter a NeoLoad Web (SaaS) token',
            'validate': EmptyValidator,
        },
        {
            'type': 'input',
            'name': 'zone',
            'message': 'Enter a NeoLoad Web Zone ID',
            'validate': EmptyValidator,
        },
        # {
        #     'type': 'input',
        #     'name': 'url',
        #     'message': 'Enter your NeoLoad Web API URL (default is SaaS: '+getNLWSaaSAPIURL()+')',
        #     'default': getNLWSaaSAPIURL(),
        #     #'validate': EmptyValidator,
        # },
    ]
    answers = prompt(questions)
    return answers

def getCurrentProfileName():
    if conf.has(profileprefix):
        return conf.get(profileprefix)
    else:
        return None

def getCurrentProfile():
    return getProfileByName(getCurrentProfileName())

def getProfileByName(name):
    try:
        return conf.get(profileprefix+name)
    except KeyError:
        return None

def getDefaultProfileName():
    return profileprefix+"default"

def listProfiles():
    cprint("List of profiles:", "yellow")
    for key in conf.all():
        if key != profileprefix and key.startswith(profileprefix):
            justname = key.replace(profileprefix,"",1)
            cprint("   "+("*" if justname == getCurrentProfileName() else "-")+" "+justname, "yellow")

def createOrUpdateProfile(proname,url,token,zone):
    if url is None: url = getNLWSaaSAPIURL()
    profile = getProfileByName(proname)
    creating = True if profile is None else False
    if creating:
        profile = {
            "token": token,
            "url": url,
            "zone": zone,
        }
        _setCurrentProfileName(proname)
    else:
        profile["token"] = token
        profile["url"] = url
        profile["zone"] = zone

    _updateProfile(proname,profile)

    if creating:
        cprint("Created profile: " + proname, "yellow")

    return profile

def _updateProfile(proname,profile):
    conf.set(profileprefix+proname, profile)

def _setCurrentProfileName(proname):
    conf.set(profileprefix, proname)

def loadProfile(proname):

    init = False
    if proname is None:
        proname = getCurrentProfileName()
    if proname is None:
        proname = getDefaultProfileName()
        init = True

    if init:
        cprint("Because there are no profiles stored, we will create a default.", "red")
        answers = askNLWAPI()
        proname = "default"
        profile = createOrUpdateProfile(proname,getNLWSaaSAPIURL(),answers.get("token"),answers.get("zone"))
    else:
        profile = getProfileByName(proname)
        if profile is None:
            cprint("Profile '"+proname+"' does not exist!", "red")
            if prompt({
                'type': 'confirm',
                'name': 'create',
                'message': "Would you like to create a new profile named '"+proname+"'?",
                'default': False,
            }).get("create"):
                answers = askNLWAPI()
                profile = createOrUpdateProfile(proname,getNLWSaaSAPIURL(),answers.get("token"),answers.get("zone"))
            else:
                return None
        else:
            _setCurrentProfileName(proname)


    cprint("Current profile: "+proname, "yellow")
    #cprint("Profile["+proname+"]"+json.dumps(profile), "blue")

    cprint("   Using NLW URL: "+profile.get("url"), "yellow")

    if profile.get("zone") is not None:
        cprint("   Profile zone: "+profile.get("zone"), "yellow")
    else:
        cprint("   No zone set. Use --zone argument.", "red")

    if profile.get("token") is None:
        cprint("   No token set. Use --token argument.", "red")

def setZone(zoneId):
    proname = getCurrentProfileName()
    if proname is None:
        proname = getDefaultProfileName()
    profile = getProfileByName(proname)
    profile["zone"] = zoneId
    _updateProfile(proname, profile)
    cprint("Profile["+proname+"] zone: "+profile.get("zone"), "green")

def setToken(token):
    proname = getCurrentProfileName()
    if proname is None:
        proname = getDefaultProfileName()
    profile = getProfileByName(proname)
    profile["token"] = token
    _updateProfile(proname, profile)
    cprint("Profile["+proname+"] token set", "green")
