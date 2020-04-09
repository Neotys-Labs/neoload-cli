import os
import urllib.parse as urlparse

import requests

from neoload_cli_lib import user_data

__current_command = ""
__current_sub_command = ""


def set_current_command(command: str):
    global __current_command
    global __current_sub_command
    __current_command = command
    __current_sub_command = ""


def set_current_sub_command(command: str):
    global __current_sub_command
    __current_sub_command = command


def get(endpoint: str):
    return get_raw(endpoint).json()


def get_raw(endpoint: str):
    return requests.get(__create_url(endpoint), headers=__create_additional_headers())


def post(endpoint: str, data):
    response = requests.post(__create_url(endpoint), headers=__create_additional_headers(), json=data)
    return response.json()


def __create_url_file_storage(endpoint):
    return urlparse.urljoin(user_data.get_user_data().get_file_storage_url(), endpoint)


def get_from_file_storage(endpoint: str):
    return requests.get(__create_url_file_storage(endpoint), headers=__create_additional_headers())


def post_binary_files_storage(endpoint: str, path):
    filename = os.path.basename(path)

    multipart_form_data = {
        'file': (filename, open(path, 'rb')),
    }

    response = requests.post(__create_url(endpoint), files=multipart_form_data)
    return response.json()


def get_file_storage(endpoint: str):
    response = requests.get(__create_url_file_storage(endpoint), headers=__create_additional_headers())
    return response.json()


def put(endpoint: str, data):
    response = requests.put(__create_url(endpoint), headers=__create_additional_headers(), json=data)
    return response.json()


def patch(endpoint: str, data):
    response = requests.patch(__create_url(endpoint), headers=__create_additional_headers(), json=data)
    return response.json()


def delete(endpoint: str):
    return requests.delete(__create_url(endpoint), headers=__create_additional_headers())


def __create_url(endpoint: str):
    return urlparse.urljoin(user_data.get_user_data().get_url(), endpoint)


def __create_additional_headers():
    return {
        'accountToken': user_data.get_user_data().get_token(),
        'accept': 'application/json',
        'User-Agent': 'NeoloadCli/' + __current_command + '/' + __current_sub_command
    }
