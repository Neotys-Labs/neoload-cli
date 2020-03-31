import click


@click.group()
def cli():
    """create/read/update/delete test settings"""
    pass


@cli.command()
def ls():
    pass


@cli.command()
def create():
    pass


@cli.command()
def update():
    pass


@cli.command()
def delete():
    pass


@cli.command()
@click.option('--numeric', is_flag=True, default=False, help="The id is number of ordering instead of uuid")
@click.argument('id')
def default(id, numeric):
    """Set the default test settings"""
    pass
