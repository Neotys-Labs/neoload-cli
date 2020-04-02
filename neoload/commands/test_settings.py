import click
import sys
import json
from neoload_cli_lib import rest_crud

__endpoint = "v2/tests"


@click.group()
@click.pass_context
def cli(ctx):
    """create/read/update/delete test settings"""
    pass


@cli.command()
@click.option('--id', 'is_id', is_flag=True, default=False, help="Use uuid instead of name")
@click.option('--pretty', is_flag=True, default=False, help="")
@click.argument('name', type=str, required=False)
def ls(name, is_id, pretty):
    endpoint = __endpoint
    if name:
        endpoint = get_end_point(name, is_id)
    result = rest_crud.get(endpoint)
    print(json.dumps(result, indent=2))


@cli.command()
def create():
    if sys.stdin.isatty():
        pass


@cli.command()
@click.argument('name', type=str, required=False)
@click.option('--id', 'is_id', is_flag=True, default=False, help="Use uuid instead of name")
def update(name, is_id):
    pass


@cli.command()
@click.option('--id', 'is_id', is_flag=True, default=False, help="Use uuid instead of name")
@click.argument('name', required=False)
def delete(name, is_id):
    pass


@cli.command()
@click.option('--id', 'is_id', is_flag=True, default=False, help="Use uuid instead of name")
@click.argument('name')
def use(name, is_id):
    """Set the default test settings"""
    if name:
        pass
    pass


def get_end_point(name: str, is_id: bool):
    if not is_id:
        pass
    return __endpoint + "/" + name


def prettify(json):
    print(json.dumps(json, indent=2))
