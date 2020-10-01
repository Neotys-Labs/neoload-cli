import urllib.parse as urlparse

import click

from commands import test_results
from neoload_cli_lib import user_data, tools

meta_key = 'result id'


@click.command()
@click.argument('name', type=str)
def cli(name):
    """get logs url of a test result managed by NeoLoad Web"""

    print(get_url(name))


def get_url(name: str):
    return urlparse.urljoin(user_data.get_user_data().get_frontend_url(), get_endpoint(name))


def get_endpoint(name: str):
    if name == "cur":
        name = user_data.get_meta(meta_key)
    is_id = tools.is_id(name)

    __id = tools.get_id(name, test_results.__resolver, is_id)

    if not __id:
        __id = user_data.get_meta_required(meta_key)

    return '#!result/%s/overview' % __id
