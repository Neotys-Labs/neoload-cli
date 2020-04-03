import re
import sys
import click
import json
from neoload_cli_lib import rest_crud, user_data

__regex_id = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

__batch = False


def set_batch(batch: bool):
    global __batch
    __batch = batch


def is_id(chain: str):
    if chain:
        return __regex_id.match(chain)
    return False


def confirm(message: str):
    if sys.stdin.isatty() and not __batch:
        return click.confirm(message, err=True)
    return True


def ls(name, is_id_, resolver):
    endpoint = resolver.get_endpoint()
    if name:
        if is_id_:
            endpoint = endpoint + "/" + name
        else:
            json_or_id = resolver.resolve_name_or_json(name)
            if type(json_or_id) is not str:
                print_json(json_or_id)
                return
    print_json(rest_crud.get(endpoint))


def delete(endpoint, id_data, kind):
    if confirm("You will delete a " + kind + "with id: " + id_data + "Are your sure ?"):
        rest_crud.delete(endpoint + "/" + id_data)


def use(name, meta_key, resolver):
    """Set the default test settings"""
    if name:
        user_data.set_meta(meta_key, name)
    else:
        default_id = user_data.get_meta(meta_key)
        for (name, settings_id) in resolver.get_map().items():
            prefix = '* ' if default_id == settings_id else '  '
            print(prefix + name + "\t: " + settings_id)


def print_json(json_data):
    print(json.dumps(json_data, indent=2))
