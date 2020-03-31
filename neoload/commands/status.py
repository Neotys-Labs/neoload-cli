import click

@click.command()
@click.option('--uri', default="https://neoload-api.saas.neotys.com/", help="The URL of api")
@click.option('--token', prompt=True, hide_input=True, help="Token used for NeoLoad Web")
def cli(token,uri):
    """get status of neoload-cli Settings"""
    pass
