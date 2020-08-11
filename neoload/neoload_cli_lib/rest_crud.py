import logging
import urllib.parse as urlparse

import requests

from version import __version__
from neoload_cli_lib import user_data, cli_exception

__current_command = ""
__current_sub_command = ""

HTTP_TIMEOUT = 5


def request_patch(slf, *args, **kwargs):
    timeout = kwargs.pop('timeout', HTTP_TIMEOUT)
    return slf.request_orig(*args, **kwargs, timeout=timeout)


setattr(requests.sessions.Session, 'request_orig', requests.sessions.Session.request)
requests.sessions.Session.request = request_patch


def set_current_command(command: str):
    global __current_command
    global __current_sub_command
    __current_command = command
    __current_sub_command = ""


def set_current_sub_command(command: str):
    global __current_sub_command
    __current_sub_command = command


def base_endpoint_with_workspace(ws=None):
    workspace_id = ws if ws else get_workspace()
    return "v2" if workspace_id is None else "v3/workspaces/" + workspace_id


def get_workspace():
    return user_data.get_meta('workspace id')


def base_endpoint():
    return "v2" if user_data.is_version_lower_than('2.5.0') else "v3"


def get_with_pagination(endpoint: str, page_size=200):
    params = {
        'limit': page_size,
        'offset': 0
    }
    # Get first page
    all_entities = get(endpoint, params)
    params['offset'] += page_size
    # Get all other pages
    while len(all_entities) == params['offset']:
        entities = get(endpoint, params)
        # Exit the loop when the pagination is not implemented for the endpoint and the number of entities is equal to page_size
        if len(entities) == 0 or all_entities[0] == entities[0]:
            break
        all_entities += entities
        params['offset'] += page_size
    return all_entities


def get(endpoint: str, params=None):
    return __handle_error(get_raw(endpoint, params)).json()


def get_raw(endpoint: str, params=None):
    return requests.get(__create_url(endpoint), params, headers=__create_additional_headers())


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
    response.encoding = 'ISO-8859-1'
    status_code = response.status_code
    if status_code > 299:
        request = response.request
        if status_code == 401:
            raise cli_exception.CliException(
                "Server has returned 401 Access denied. Please check your token and rights")
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
