import logging
import urllib.parse as urlparse

import requests

from version import __version__
from neoload_cli_lib import user_data, cli_exception

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
    return __handle_error(get_raw(endpoint)).json()


def get_raw(endpoint: str):
    return requests.get(__create_url(endpoint), headers=__create_additional_headers())


def post(endpoint: str, data):
    logging.debug(f'POST {endpoint} body={data}')
    response = requests.post(__create_url(endpoint), headers=__create_additional_headers(), json=data)
    __handle_error(response)
    return response.json()


def __create_url_file_storage(endpoint):
    return urlparse.urljoin(user_data.get_user_data().get_file_storage_url(), endpoint)


def get_from_file_storage(endpoint: str):
    return __handle_error(requests.get(__create_url_file_storage(endpoint), headers=__create_additional_headers()))


def post_binary_files_storage(endpoint: str, path, filename):
    logging.debug(f'POST (files) {endpoint} path={path} filename={filename}')
    multipart_form_data = {
        'file': (filename, path),
    }

    response = requests.post(__create_url_file_storage(endpoint), headers=__create_additional_headers(),
                             files=multipart_form_data)
    __handle_error(response)
    return response


def put(endpoint: str, data):
    logging.debug(f'PUT {endpoint} body={data}')
    response = requests.put(__create_url(endpoint), headers=__create_additional_headers(), json=data)
    __handle_error(response)
    return response.json()


def patch(endpoint: str, data):
    logging.debug(f'PATCH {endpoint} body={data}')
    response = requests.patch(__create_url(endpoint), headers=__create_additional_headers(), json=data)
    __handle_error(response)
    return response.json()


def delete(endpoint: str):
    response = requests.delete(__create_url(endpoint), headers=__create_additional_headers())
    __handle_error(response)
    return response


def __create_url(endpoint: str):
    return urlparse.urljoin(user_data.get_user_data().get_url(), endpoint)


def __handle_error(response):
    status_code = response.status_code
    if status_code > 299:
        request = response.request
        if status_code == 401:
            raise cli_exception.CliException("Server has returned 401 Access denied. Please check your token and rights")
        else:
            raise cli_exception.CliException(
                "Error " + str(status_code) + " during the request: "
                + request.method + " " + request.url + "\n" + response.text
            )
    return response


def __create_additional_headers():
    cli_version = 'dev' if __version__ is None else __version__
    return {
        'accountToken': user_data.get_user_data().get_token(),
        'accept': 'application/json',
        'User-Agent': 'NeoloadCli/' + cli_version + '/' + __current_command + '/' + __current_sub_command
    }
