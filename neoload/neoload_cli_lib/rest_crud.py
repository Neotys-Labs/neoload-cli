import requests
import urllib.parse as urlparse
from neoload_cli_lib import user_data


def get(endpoint: str):
    response = requests.get(__create_url(endpoint), headers=__create_additional_headers())
    return response.json()


def post(endpoint: str, data):
    response = requests.get(__create_url(endpoint), headers=__create_additional_headers(), data=data)
    return response.json()


def put(endpoint: str, data):
    response = requests.put(__create_url(endpoint), headers=__create_additional_headers(), data=data)
    return response.json()


def patch(endpoint: str, data):
    response = requests.patch(__create_url(endpoint), headers=__create_additional_headers(), data=data)
    return response.json()


def delete(endpoint: str):
    response = requests.delete(__create_url(endpoint), headers=__create_additional_headers())
    return response.json()


def __create_url(endpoint: str):
    return urlparse.urljoin(user_data.get_user_data().get_url(), endpoint)


def __create_additional_headers():
    return {
        'accountToken': user_data.get_user_data().get_token(),
        'accept': 'application/json',
        'User-Agent': 'NeoloadCli'
    }
