import appdirs
import os
import yaml

__conf_name = "neoload-cli"
__version = "1.0"
__author = "neotys"
__config_dir = appdirs.user_data_dir(__conf_name, __author, __version)
__config_file = os.path.join(__config_dir, "config.yaml")
__yaml_schema_file = os.path.join(__config_dir, "yaml_schema.json")

__no_write = False


def do_logout():
    global __user_data_singleton
    __user_data_singleton = None
    os.remove(__config_file)


def get_user_data(throw=True):
    if __user_data_singleton is None and throw:
        raise Exception("You are'nt logged. Please use command \"neoload login\" first")
    return __user_data_singleton


def do_login(token, url, no_write):
    global __no_write
    __no_write = no_write
    if token is None:
        raise Exception('token is mandatory. please see neoload login --help.')
    global __user_data_singleton
    __user_data_singleton = UserData.from_login(token, url)
    __save_user_data()
    return __user_data_singleton


class UserData:
    def __init__(self, token=None, url=None, desc=None):
        self.metadata = {}
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
        metadata = ""
        for (key, value) in self.metadata.items():
            metadata += key + ": " + value + "\n"
        return "You are logged on " + self.url + " with token " + token + "\n" + metadata

    def get_url(self):
        return self.url

    def get_frontend_url(self):
        return self.url.replace('-api', '')

    def get_token(self):
        return self.token


def __load_user_data():
    if os.path.exists(__config_file):
        with open(__config_file, "r") as stream:
            load = yaml.load(stream, Loader=yaml.BaseLoader)
            return UserData.from_dict(load)

    return None


__user_data_singleton = __load_user_data()


def __save_user_data():
    if not __no_write:
        os.makedirs(__config_dir, exist_ok=True)
        with open(__config_file, "w") as stream:
            yaml.dump(__user_data_singleton.__dict__, stream)


def set_meta(key, value):
    get_user_data().metadata[key] = value
    __save_user_data()


def get_meta(key):
    return get_user_data().metadata.get(key, None)


def __load_yaml_schema():
    if os.path.exists(__yaml_schema_file):
        with open(__yaml_schema_file, "r") as stream:
            return stream.read()
    return None


__yaml_schema_singleton = __load_yaml_schema()


def get_yaml_schema(throw=True):
    if __yaml_schema_singleton is None and throw:
        raise Exception("No yaml schema found. Please add --schema-url option to download it first")
    return __yaml_schema_singleton


def update_schema(yaml_schema_as_json: str):
    global __yaml_schema_singleton
    __yaml_schema_singleton = yaml_schema_as_json
    os.makedirs(__config_dir, exist_ok=True)
    with open(__yaml_schema_file, "w") as stream:
        stream.write(__yaml_schema_singleton)
