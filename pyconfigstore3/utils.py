import os
import sys
import json

def getConfigDir():
    if sys.platform == "win32":
        app_config_dir = os.getenv("LOCALAPPDATA")
    else:
        app_config_dir = os.getenv("HOME")
        if os.getenv("XDG_CONFIG_HOME"):
            app_config_dir = os.getenv("XDG_CONFIG_HOME")


    configDir = os.path.join(app_config_dir, ".localconfig")
    return configDir

def createPath(path):
    if not os.path.exists(path):
        os.makedirs(path, 0o777)
        return True

def createConfig(path, defaults, **kwargs):
    configDir = getConfigDir()
    pathEntry = os.path.join(configDir, kwargs["pathEntry"])
    createPath(pathEntry)
    if os.path.exists(pathEntry) and not os.path.isfile(path):
        with open(path, 'w') as cf:
            json.dump(defaults, cf)


def createConfigPathSync(path):
    pathEntry = os.path.dirname(path)
    createConfig(path, {}, pathEntry=pathEntry)


def loadConfigs(path):
    createConfigPathSync(path)
    if os.path.isfile(path):
        with open(path, 'r') as fp:
            jsonConfigs = dict(json.load(fp))
        return jsonConfigs

def writeConfigs(path, jsonData):
    with open(path, 'w') as fp:
        json.dump(jsonData, fp)

def setConfigs(path, key=None, value=None, Object=None):

    jsonConfigs = loadConfigs(path)
    if Object == None:
        jsonConfigs.update(dotnotation(key, value))
    else:
        for jkey, jval in Object.items():
            jsonConfigs.update(dotnotation(jkey,jval))
    writeConfigs(path, jsonConfigs)

def getConfigs(path, key):
    jsonConfigs = loadConfigs(path)
    value = jsonConfigs[key]
    return value

def hasConfigs(path, key):
    jsonConfigs = loadConfigs(path)
    if key in jsonConfigs:
        return True
    return False

def deleteConfigs(path, key):
    jsonConfigs = loadConfigs(path)
    jsonConfigs.pop(key)
    writeConfigs(path, jsonConfigs)

def clearConfigs(path):
    writeConfigs(path, {})


def getConfigSize(path):
    jsonConfigs = loadConfigs(path)
    return len(jsonConfigs)

def dotnotation(key, value):

    key = key.replace("\\.", "~=~")
    keyArr = key.split('.')[::-1]
    for arr in keyArr:
        value = {arr.replace('~=~', '.'):value}
    return value
