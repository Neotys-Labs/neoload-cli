import click


@click.command()
@click.argument("name_or_id", type=str)
@click.option("--scenario", help="select scenario")
@click.option("--name", help="name of test results")
@click.option("-d", "--detached",help="Doesn't wait the end of test")
def cli(name_or_id, scenario, detached, name):
    """run a test"""

    pass
