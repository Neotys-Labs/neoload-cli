import click

import neoload_cli_lib


@click.command()
@click.option('--uri', default="https://neoload-api.saas.neotys.com/", help="The URL of api ", metavar='URL')
@click.argument('token', required=False)  # prompt=True, hide_input=True, help="Token used for NeoLoad Web",
def cli(token, uri):
    """Store your token and uri of NeoLoad Web. The token is read from stdin if none is set.
    wThe default url is "https://neoload-api.saas.neotys.com/" """
    neoload_cli_lib.UserData.do_login(token, uri)
