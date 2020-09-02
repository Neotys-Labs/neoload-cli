import urllib.parse as urlparse

import click

from commands import test_results
from neoload_cli_lib import user_data, tools

from neoload_cli_lib.name_resolver import Resolver
from neoload_cli_lib import rest_crud, user_data

__endpoint = "/test-results"

__resolver = Resolver(__endpoint, rest_crud.base_endpoint_with_workspace)

meta_key = 'result id'

@click.command()
@click.argument('name', type=str)
def cli(name):
    """get logs url of a test result managed by NeoLoad Web"""

    if name == "cur":
        name = user_data.get_meta(meta_key)
    is_id = tools.is_id(name)

    __id = tools.get_id(name, __resolver, is_id)

    if not __id:
        __id = user_data.get_meta_required(meta_key)

    print(get_url(name))


def get_url(name: str):
    return urlparse.urljoin(user_data.get_user_data().get_frontend_url(), get_endpoint(name))


def get_endpoint(name: str):
    __id = tools.get_id(name, test_results.__resolver)
    return '#!result/%s/overview' % __id
