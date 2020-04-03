import click
import sys
import json

from neoload_cli_lib import tools, rest_crud
from neoload_cli_lib.name_resolver import Resolver

__endpoint = "v2/test-results"

__resolver = Resolver(__endpoint)

meta_key = 'result id'


@click.command()
@click.argument('command', type=click.Choice(['ls', 'put', 'patch', 'delete', 'use'], case_sensitive=False),
                required=False)
@click.argument("name", type=str, required=False)
@click.option('--rename', help="")
@click.option('--description', help="")
@click.option('--quality-status', 'quality_status', help="")
def cli(command, name, rename, description, quality_status):
    """create/read/update/delete test settings"""
    if not command:
        print("command is mandatory. Please see neoload tests-settings --help")
        return
    is_id = tools.is_id(name)
    # avoid to make two requests if we have not id.
    if command == "ls":
        tools.ls(name, is_id, __resolver)
        return

    __id = get_id(name, is_id)

    if command == "put":
        rest_crud.put(get_end_point(__id), create_json(rename, description, quality_status))
    elif command == "delete":
        tools.delete(__endpoint, __id, "test results")
    elif command == "use":
        tools.use(__id, meta_key, __resolver)


def get_id(name, is_id):
    if is_id or not name:
        return name
    else:
        return __resolver.resolve_name(name)


def get_end_point(id_test: str):
    return __endpoint + "/" + id_test


def create_json(name, description, quality_status):
    data = {}
    if name is not None:
        data['name'] = name
    if description is not None:
        data['description'] = description
    if quality_status is not None:
        data['qualityStatus'] = quality_status

    if len(data) == 0:
        if sys.stdin.isatty():
            for field in ['name', 'description', 'qualityStatus']:
                data[field] = input(field)
        else:
            return json.load(sys.stdin.read())
    return data
