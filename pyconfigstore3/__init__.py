import os
from os.path import join
import sys
import json
from .utils import *


class ConfigStore:



    def __init__(self, name, defaults={}, globalConfigPath=False):
        self.name = name
        self.defaults = defaults
        self.globalConfigPath = globalConfigPath

        self.configDir = getConfigDir()

        # override is for testing purposes, to maintain hermetic test-only config
        overrideName = os.getenv("PYCONFIGSTORE_NAME_OVERRIDE")
        if overrideName is not None and overrideName != "":
            name = overrideName

        if self.globalConfigPath:
            self.pathPrefix = join(name, 'config.json')
            pathEntry = name
        else:
            self.pathPrefix = join('configstore', '{}.json'.format(name))
            pathEntry = 'configstore'

        self.path = join(self.configDir, self.pathPrefix)
        # self.all = {}
        createConfig(self.path, self.defaults, pathEntry=pathEntry)
        self.Object = loadConfigs(self.path)
        self.size = getConfigSize(self.path)


    def all(self, Object=None):
        if Object:
            self.set(Object)

        jsonConfigs = loadConfigs(self.path)
        return jsonConfigs

    def get(self, key):
        value = getConfigs(self.path, key)
        return value

    def set(self, key, value=None):
        if isinstance(key, dict):
            setObject = key
            setConfigs(self.path, Object=setObject)
        else:
            if not value:
                raise KeyError("KeyError: param value not provided")

            setConfigs(self.path, key=key, value=value)

    def has(self, key):
        return hasConfigs(self.path, key)

    def delete(self, key):
        deleteConfigs(self.path, key)

    def clear(self):
        clearConfigs(self.path)
