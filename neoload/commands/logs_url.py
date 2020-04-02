import click
import urllib.parse as urlparse
from neoload_cli_lib import user_data


@click.command()
@click.option('--id', 'is_id', is_flag=True, default=False, help="Use uuid instead of name")
@click.argument('name', type=str)
def cli(name, is_id):
    """get logs url of a test result managed by NeoLoad Web"""
    print(urlparse.urljoin(user_data.get_user_data().getUrl(), get_endpoint(name, is_id)))


def get_endpoint(name: str, is_id: bool):
    if is_id:
        return '#!result/%s/overview' % name
