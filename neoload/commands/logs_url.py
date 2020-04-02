import click

@click.command()
@click.option('--uri', default="https://neoload-api.saas.neotys.com/", help="The URL of api")
def cli(token,uri):
    """get logs url of running test managed by NeoLoad Web"""
    pass
