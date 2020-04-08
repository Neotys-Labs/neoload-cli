import requests
import os
import json

import urllib.parse as urlparse
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
    response = requests.get(__create_url(endpoint), headers=__create_additional_headers())
    return response.json()


def post(endpoint: str, data):
    response = requests.post(__create_url(endpoint), headers=__create_additional_headers(), json=data)
    return response.json()


def post_binary(endpoint: str, path):
    filename = os.path.basename(path)

    multipart_form_data = {
        'file': (filename, open(path, 'rb')),
    }

    response = requests.post(__create_url(endpoint), files=multipart_form_data)
    return response.json()


def put(endpoint: str, data):
    response = requests.put(__create_url(endpoint), headers=__create_additional_headers(), json=data)
    return response.json()


def patch(endpoint: str, data):
    response = requests.patch(__create_url(endpoint), headers=__create_additional_headers(), json=data)
    return response.json()


def delete(endpoint: str):
    response = requests.delete(__create_url(endpoint), headers=__create_additional_headers())
    if response.text == '':
        return json.loads('{"code":"%s","ok":"%s"}' % (response.status_code, response.ok))
    return response.json()


def __create_url(endpoint: str):
    return urlparse.urljoin(user_data.get_user_data().get_url(), endpoint)


def __create_additional_headers():
    return {
        'accountToken': user_data.get_user_data().get_token(),
        'accept': 'application/json',
        'User-Agent': 'NeoloadCli/' + __current_command + '/' + __current_sub_command
    }
