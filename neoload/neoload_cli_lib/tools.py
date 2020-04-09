import re
import sys
import click
import json

from click import ClickException

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


def get_named_or_id(name, is_id_, resolver):
    endpoint = resolver.get_endpoint()
    if not is_id_:
        json_or_id = resolver.resolve_name_or_json(name)
        if type(json_or_id) is not str:
            return json_or_id
        else:
            name = json_or_id

    return rest_crud.get(endpoint + "/" + name)


def ls(name, is_id_, resolver):
    endpoint = resolver.get_endpoint()
    if name:
        get_id_and_print_json(get_named_or_id(name, is_id_, resolver))
    else:
        print_json(rest_crud.get(endpoint))


def delete(endpoint, id_data, kind):
    if confirm("You will delete a " + kind + " with id: " + id_data + " Are your sure ?"):
        return rest_crud.delete(endpoint + "/" + id_data)
    raise click.Abort


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


def get_id_and_print_json(json_data: json):
    print_json(json_data)
    if 'id' not in json_data:
        raise ClickException('No uui returned. Operation may have failed !')
    return json_data['id']


def is_integer(string):
    try:
        int(string)
        return True
    except ValueError:
        return False
