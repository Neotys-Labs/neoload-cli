import click

@click.command()
@click.argument("name_or_id", type=str, required=False)
def cli():
    """read of NeoLoad Web zones"""

    pass
