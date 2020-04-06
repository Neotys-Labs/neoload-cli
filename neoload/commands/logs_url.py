import click
import urllib.parse as urlparse
from commands.test_results import get_id
from neoload_cli_lib import user_data, tools


@click.command()
@click.argument('name', type=str)
def cli(name):
    """get logs url of a test result managed by NeoLoad Web"""
    print(urlparse.urljoin(user_data.get_user_data().get_frontend_url(), get_endpoint(name)))


def get_endpoint(name: str):
    __is_id = tools.is_id(name)
    __id = get_id(name, __is_id)
    return '#!result/%s/overview' % __id
