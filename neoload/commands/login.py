import sys
import click

from neoload_cli_lib import user_data


@click.command()
@click.option('--url', default="https://neoload-api.saas.neotys.com/", help="The URL of api ", metavar='URL')
@click.option('--no-write', is_flag=True, help="don't save login on application data")
@click.argument('token', required=False)
def cli(token, url, no_write):
    """Store your token and uri of NeoLoad Web. The token is read from stdin if none is set.
    The default url is "https://neoload-api.saas.neotys.com/" """
    if not token:
        if sys.stdin.isatty():
            token = click.prompt("Enter your token", None, True)
        else:
            token = input()

    __user_data = user_data.do_login(token, url, no_write)
    if sys.stdin.isatty():
        print(__user_data)
