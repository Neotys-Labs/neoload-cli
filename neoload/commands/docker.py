import click


@click.command()
@click.argument("command", required=True)
@click.argument("path", required=False, type=click.Path(exists=True))
@click.argument("name_or_id", type=str)
def cli(command):
    """Upload a project to settings"""
    pass  # TODO