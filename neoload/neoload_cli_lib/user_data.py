import appdirs
import os
import yaml

__conf_name = "neoload-cli"
__version = "1.0"
__author = "neotys"
__config_dir = appdirs.user_data_dir(__conf_name, __author, __version)
__config_file = os.path.join(__config_dir, "config.yaml")


def do_logout():
    global __user_data_singleton
    __user_data_singleton = None
    os.remove(__config_file)


def get_user_data(throw=True):
    if __user_data_singleton is None and throw:
        raise Exception("You are'nt logged. Please use command \"neoload login\" first")
    return __user_data_singleton


def do_login(token, url, no_write):
    if token is None:
        raise Exception('token is mandatory. please see neoload login --help.')
    global __user_data_singleton
    __user_data_singleton = UserData.from_login(token, url)
    if not no_write:
        __save()
    return __user_data_singleton


class UserData:
    def __init__(self, token=None, url=None, desc=None):
        if desc:
            self.__dict__.update(desc)
        else:
            self.token = token
            self.url = url

    @staticmethod
    def from_dict(entries):
        return UserData(desc=entries)

    @staticmethod
    def from_login(token: str, url: str):
        return UserData(token, url)

    def __str__(self):
        token = '*' * (len(self.token) - 3) + self.token[-3:]
        return "you are logged on " + self.url + " with token " + token

    def getUrl(self):
        return self.url

    def getToken(self):
        return self.token

def __load():
    if os.path.exists(__config_file):
        with open(__config_file, "r") as stream:
            load = yaml.load(stream, Loader=yaml.BaseLoader)
            return UserData.from_dict(load)

    return None


__user_data_singleton = __load()


def __save():
    os.makedirs(__config_dir, exist_ok=True)
    with open(__config_file, "w") as stream:
        yaml.dump(__user_data_singleton.__dict__, stream)
