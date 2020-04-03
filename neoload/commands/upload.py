import click


@click.command()
@click.argument("path", required=False, type=click.Path(exists=True))
@click.argument("name_or_id", type=str)
def cli(name_or_id, path):
    """Upload a project to settings"""
    pass
