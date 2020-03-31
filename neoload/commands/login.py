import click

from neoload_cli_lib.UserData import UserData


@click.command()
@click.option('--uri', default="https://neoload-api.saas.neotys.com/", help="The URL of api ", metavar='URL')
@click.argument('token', required=False)  # prompt=True, hide_input=True, help="Token used for NeoLoad Web",
def cli(token, uri):
    """Store your token and uri of NeoLoad Web. The token is read from stdin if none is set.
    The default url is "https://neoload-api.saas.neotys.com/" """
    if token is None:
        token = click.prompt("Enter your token", None, True)
    UserData.do_login(token, uri)
