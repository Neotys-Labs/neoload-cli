import click

@click.command()
@click.option('--uri', default="https://neoload-api.saas.neotys.com/", help="The URL of api")
@click.option('--token', prompt=True, hide_input=True, help="Token used for NeoLoad Web")
def cli(token,uri):
    """create/read/update/delete of NeoLoad Web zones"""
    pass
