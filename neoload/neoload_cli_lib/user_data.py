import os
import re
import sys

import appdirs
import requests
import yaml
from simplejson import JSONDecodeError

from neoload_cli_lib import rest_crud, cli_exception, tools, config_global

__conf_name = "neoload-cli"
__version = "1.0"
__author = "neotys"
__config_dir = appdirs.user_data_dir(__conf_name, __author, __version)
__local_file = ".neoload_cli.yaml"
CONFIG_FILE = __local_file if os.path.exists(__local_file) else os.path.join(__config_dir, "config.yaml")
__yaml_schema_file = os.path.join(__config_dir, "yaml_schema.json")

__no_write = False


def do_logout():
    UserData.clean()
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)


def get_user_data(throw=True):
    instance = UserData.get_instance()
    if instance is None and throw:
        raise cli_exception.CliException("You aren't logged. Please use command \"neoload login\" first")
    return instance


def do_login(token, url, no_write, ssl_cert='', local_config=False):
    global __no_write
    __no_write = no_write
    if token is None:
        raise cli_exception.CliException('token is mandatory. please see neoload login --help.')

    __user_data_singleton = UserData.from_login(token, url)
    if not __no_write:
        __user_data_singleton.set_file(__local_file if local_config else CONFIG_FILE)
    __user_data_singleton.set_ssl_cert(ssl_cert)
    __compute_version_and_path()
    __save_user_data()
    return __user_data_singleton


def get_front_url_by_private_entrypoint():
    response = rest_crud.get('/nlweb/rest/rest-api/url-api/v1/action/get-front-end-url')
    return response['frontEndUrl']['rootUrl']


def __compute_version_and_path():
    if get_nlweb_information() is False:
        file_storage = get_file_storage_from_swagger()
        front = get_front_url_by_private_entrypoint()
        UserData.get_instance().set_url(front, file_storage, None)


def get_file_storage_from_swagger():
    response = rest_crud.get_raw('explore/v2/swagger.yaml')
    spec = yaml.load(response.text, Loader=yaml.FullLoader)
    if isinstance(spec, str) or 'basestring' in "{}".format(type(spec)) or 'paths' not in spec.keys():
        raise cli_exception.CliException(
            'Unable to reach Neoload Web API. Bad URL or bad swagger file at /explore/v2/swagger.yaml.'
        )
    return spec['paths']['/tests/{testId}/project']['servers'][0]['url']


def get_nlweb_information():
    try:
        response = rest_crud.get_raw('v3/information')
        if response.status_code == 401:
            raise cli_exception.CliException(response.text)
        elif response.status_code == 200:
            json = response.json()
            UserData.get_instance().set_url(json['front_url'], json['filestorage_url'], json['version'])
            return True
        else:
            return False
    except requests.exceptions.MissingSchema as err:
        raise cli_exception.CliException('Unable to reach Neoload Web API. The URL must start with https:// or http://'
                                         + '. Details: ' + str(err))
    except requests.exceptions.ConnectionError as err:
        raise cli_exception.CliException('Unable to reach Neoload Web API. Bad URL. Details: ' + str(err))
    except JSONDecodeError as err:
        raise cli_exception.CliException('Unable to parse the response of the server. Did you set the frontend URL'
                                         + ' instead of the API url ? Details: ' + str(err))


class UserData:
    __instance = None

    @staticmethod
    def get_instance():
        if UserData.__instance is None and os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as stream:
                load = yaml.load(stream, Loader=yaml.BaseLoader)
                loaded = UserData(desc=load)
                loaded.file = CONFIG_FILE
                UserData.__instance = loaded if loaded.token else None

        return UserData.__instance

    @staticmethod
    def from_login(token: str, url: str):
        UserData.__instance = UserData(token, url)
        return UserData.__instance

    @staticmethod
    def clean():
        UserData.__instance = None

    def __init__(self, token=None, url=None, desc=None):
        self.metadata = {}
        self.resolved_ids = {}
        self.file = None
        if desc:
            self.__dict__.update(desc)
        else:
            self.token = token
            self.url = url

    def __str__(self):
        token = '*' * (len(self.token) - 3) + self.token[-3:]
        metadata = ""
        for (key, value) in self.metadata.items():
            if value is not None:
                metadata += key + ": " + str(value) + self.prettify_resolved(key, value) + "\n"
        if self.file:
            metadata += "\nThe configuration file is: " + os.path.realpath(self.file) + "\n"
        return "You are logged on " + self.url + " with token " + token + "\n\n" + metadata

    def prettify_resolved(self, key, value):
        resolved_map = self.resolved_ids.get(key)
        if resolved_map:
            resolved_value = resolved_map.get(str(value))
            return ' ({})'.format(resolved_value) if resolved_value else ""
        return ''

    def get_url(self):
        return self.url

    def get_frontend_url(self):
        return self.metadata['frontend url']

    def get_token(self):
        return self.token

    def get_file_storage_url(self):
        return self.metadata['file storage url']

    def get_version(self):
        return self.metadata['version']

    def set_url(self, frontend, files_storage, version):
        if frontend:
            self.metadata['frontend url'] = frontend
        if files_storage:
            self.metadata['file storage url'] = files_storage
        if version:
            self.metadata['version'] = version
        else:
            self.metadata['version'] = 'legacy'

    def set_ssl_cert(self, ssl_cert):
        if ssl_cert:
            self.metadata['ssl certificate'] = ssl_cert

    def set_file(self, file):
        self.file = file


def get_ssl_cert():
    return tools.ssl_cert_to_verify(UserData.get_instance().metadata.get('ssl certificate'))


def __save_user_data():
    if not __no_write:
        instance = UserData.get_instance()
        dest_file = os.path.abspath(instance.file or CONFIG_FILE)
        config_dir = os.path.dirname(dest_file)
        os.makedirs(config_dir, exist_ok=True)
        with open(dest_file, "w") as stream:
            yaml.dump(instance.__dict__, stream)


def set_meta(key, value):
    if value is None:
        get_user_data().metadata.pop(key, None)
    else:
        get_user_data().metadata[key] = value
    __save_user_data()


def put_resolved_map(key, values, save=True):
    if values is None:
        get_user_data().resolved_ids.pop(key, None)
    else:
        get_user_data().resolved_ids[key] = {v: k for k, v in values.items()}

    if save:
        __save_user_data()


def get_meta(key):
    result = get_user_data().metadata.get(key, None)
    if result == 'null':
        result = None
    return result


def is_version_lower_than(version: str):
    return __version_to_int(get_user_data().get_version()) < __version_to_int(version)


def __version_to_int(version: str):
    if version.lower() == 'saas':
        return sys.maxsize
    elif version.lower() == 'legacy':
        return -1

    version_as_int = 0
    offset = 1
    # Only keep numbers on the version (remove -SNAPSHOT for example)
    for digit in reversed(re.sub('[^0-9\\.]*', '', version).split('.')):
        version_as_int += int(digit) * offset
        offset *= 1000
    return version_as_int


def get_meta_required(key):
    if key not in get_user_data().metadata:
        raise cli_exception.CliException('No name or id provided. Please specify the object name or id.')
    return get_user_data().metadata.get(key)


def __load_yaml_schema():
    if os.path.exists(__yaml_schema_file):
        with open(__yaml_schema_file, "r") as stream:
            return stream.read()
    return None


__yaml_schema_singleton = __load_yaml_schema()


def get_yaml_schema(throw=True):
    if __yaml_schema_singleton is None and throw:
        raise cli_exception.CliException("No yaml schema found. Please add --refresh option to download it first")
    return __yaml_schema_singleton


def update_schema(yaml_schema_as_json: str):
    global __yaml_schema_singleton
    __yaml_schema_singleton = yaml_schema_as_json
    os.makedirs(__config_dir, exist_ok=True)
    with open(__yaml_schema_file, "w") as stream:
        stream.write(__yaml_schema_singleton)
