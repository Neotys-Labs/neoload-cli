import urllib.parse as urlparse

import click

from commands import test_results
from neoload_cli_lib import user_data, tools


@click.command()
@click.argument('name', type=str)
def cli(name):
    """get logs url of a test result managed by NeoLoad Web"""

    print(get_url(name))


def get_url(name: str):
    return urlparse.urljoin(user_data.get_user_data().get_frontend_url(), get_endpoint(name))


def get_endpoint(name: str):
    __id = tools.get_id(name, test_results.__resolver)
    return '#!result/%s/overview' % __id
