import logging
import os
import sys
import urllib.parse as urlparse
from inspect import stack

import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from tqdm import tqdm

from neoload_cli_lib import user_data, cli_exception, tools
from version import __version__

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Overrides parse_retry_after
Retry.parse_retry_after = lambda self, retry_after: custom_parse_retry_after(retry_after)
retry_strategy = Retry(
    total=10,
    status_forcelist=[429],
    allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

__current_command = ""
__current_sub_command = ""
__agents_already_sent = set()


def set_current_command():
    global __current_command
    global __current_sub_command
    # Find the command name by getting the caller's filePath from the stacktrace, extractBaseName and remove extension
    __current_command = os.path.splitext(os.path.basename(stack()[1].filename))[0]
    __current_sub_command = ""


def set_current_sub_command(command: str):
    global __current_sub_command
    __current_sub_command = command


def custom_parse_retry_after(retry_after: str):
    retry_after_seconds = int(retry_after) / 1000 if int(retry_after) > 0 else 0
    logging.getLogger().warning(
        f'WARNING: Too many requests, server rate limit reached. Retry in {retry_after_seconds} seconds.')
    return retry_after_seconds


def base_endpoint_with_workspace(ws=None):
    workspace_id = ws if ws else get_workspace()
    return "v2" if workspace_id is None else "v3/workspaces/" + workspace_id


def get_workspace():
    return user_data.get_meta('workspace id')


def base_endpoint():
    return "v2" if user_data.is_version_lower_than('2.5.0') else "v3"


def get_with_pagination(endpoint: str, page_size=200, api_query_params=None):
    params = {
        'limit': page_size,
        'offset': 0
    }
    params.update(api_query_params or {})  # Add query params for filters

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
    return http.get(__create_url(endpoint), params=params, headers=__create_additional_headers(),
                    verify=user_data.get_ssl_cert())


def post(endpoint: str, data):
    logging.debug(f'POST {endpoint} body={data}')
    response = http.post(__create_url(endpoint), headers=__create_additional_headers(), json=data,
                         verify=user_data.get_ssl_cert())
    __handle_error(response)
    return response.json()


def __create_url_file_storage(endpoint):
    return urlparse.urljoin(user_data.get_user_data().get_file_storage_url(), endpoint)


def get_from_file_storage(endpoint: str):
    return __handle_error(http.get(__create_url_file_storage(endpoint), headers=__create_additional_headers(),
                                   verify=user_data.get_ssl_cert()))


def post_binary_files_storage(endpoint: str, path, filename):
    logging.debug(f'POST (files) {endpoint} path={path} filename={filename}')
    multipart_form_data, bar = multipart_progress(path, filename)
    headers = __create_additional_headers()
    headers['Content-Type'] = multipart_form_data.content_type
    response = http.post(__create_url_file_storage(endpoint), headers=headers,
                         data=multipart_form_data, verify=user_data.get_ssl_cert())
    if bar:
        bar.close()
    __handle_error(response)
    return response


def multipart_progress(path, filename):
    encoder = MultipartEncoder({'file': (filename, path, 'application/octet-stream')})
    if tools.is_user_interactive():
        bar = tqdm(desc=filename,
                   total=encoder.len,
                   leave=False,
                   dynamic_ncols=True,
                   unit='B',
                   unit_scale=True,
                   unit_divisor=1024)
        multipart_monitor = MultipartEncoderMonitor(encoder, lambda monitor: bar.update(monitor.bytes_read - bar.n))
        return multipart_monitor, bar
    else:
        return encoder, None


def put(endpoint: str, data):
    logging.debug(f'PUT {endpoint} body={data}')
    response = http.put(__create_url(endpoint), headers=__create_additional_headers(), json=data,
                        verify=user_data.get_ssl_cert())
    __handle_error(response)
    return response.json()


def patch(endpoint: str, data):
    logging.debug(f'PATCH {endpoint} body={data}')
    response = http.patch(__create_url(endpoint), headers=__create_additional_headers(), json=data,
                          verify=user_data.get_ssl_cert())
    __handle_error(response)
    return response.json()


def delete(endpoint: str):
    response = http.delete(__create_url(endpoint), headers=__create_additional_headers(),
                           verify=user_data.get_ssl_cert())
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
    headers = {
        'accountToken': user_data.get_user_data().get_token(),
        'accept': 'application/json'
    }
    add_user_agent(headers)
    return headers


def add_user_agent(headers):
    global __agents_already_sent
    # Add a user agent to headers only once per CLI command/subcommand
    if f'{__current_command}{__current_sub_command}' not in __agents_already_sent:
        __agents_already_sent.add(f'{__current_command}{__current_sub_command}')
        cli_version = 'dev' if __version__ is None else __version__
        cli_version += "-interactive" if sys.stdin.isatty() and not tools.are_any_ci_env_vars_active() else "-automated"
        headers.setdefault('User-Agent',
                           'NeoloadCli/' + cli_version + '/' + __current_command + '/' + __current_sub_command)
