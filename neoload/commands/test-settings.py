import click
import sys
from neoload_cli_lib import RestCrud

@click.group()
def cli():
    """create/read/update/delete test settings"""
    pass


@cli.command()
@click.argument('id', required=False)
def get(id):
    endpoint = "test"
    if id:
        endpoint += "/" + id
    print(RestCrud.get(endpoint))

@cli.command()
def create():
    if sys.stdin.isatty():
        pass



@cli.command()
@click.option('--id', is_flag=True, default=False, help="The use uuid instead of name")
def update(name, id):
    pass


@cli.command()
@click.option('--id', is_flag=True, default=False, help="The use uuid instead of name")
@click.argument('name', required=False)
def delete(name, id):
    pass



@cli.command()
@click.option('--id', is_flag=True, default=False, help="The use uuid instead of name")
@click.argument('name')
def use(name):
    """Set the default test settings"""
    if name:
        pass
    pass
