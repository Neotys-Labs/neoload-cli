import click

@click.group()
def cli():
    """get test results"""
    pass


@cli.command()
def ls():
    pass

@cli.command()
def summary():
    pass

@cli.command()
def update():
    pass

@cli.command()
def delete():
    pass

@cli.command()
def junitreport():
    pass