import json
import os
import re
import sys

import click
from click import ClickException
from termcolor import cprint

from neoload_cli_lib import rest_crud, user_data

__regex_id = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
__regex_mongodb_id = re.compile('[a-f\\d]{24}', re.IGNORECASE)

__batch = False


def __is_color_terminal():
    if not sys.stdout.isatty():
        return False
    if os.getenv('COLORTERM'):
        return True
    if os.getenv('TERM_PROGRAM') in {'iTerm.app', 'Hyper', 'Apple_Terminal'}:
        return True
    if os.getenv('TERM') in {'screen-256', 'screen-256color', 'xterm-256', 'xterm-256color', 'color', 'cygwin'}:
        return True
    return False


__is_color_term = __is_color_terminal()


def is_color_terminal():
    return __is_color_term


def print_color(text, color=None, on_color=None, attrs=None, **kwargs):
    if __is_color_term:
        cprint(text, color, on_color, attrs, **kwargs)
    else:
        print(text)


def set_batch(batch: bool):
    global __batch
    __batch = batch


def is_batch():
    return __batch


def is_mongodb_id(chain: str):
    if chain:
        return __regex_mongodb_id.match(chain)
    return False


def is_id(chain: str):
    if chain:
        return __regex_id.match(chain)
    return False


def confirm(message: str, quit_option=False):
    if sys.stdin.isatty() and not __batch:
        choice = ['y', 'n']
        if quit_option:
            choice.append('q')
        response = click.prompt(message, default='n', type=click.Choice(choice, case_sensitive=False), err=True)
        if quit_option and response == 'q':
            quit(0)
        return response == 'y'
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
        print_json(rest_crud.get_with_pagination(endpoint))


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
    print(json.dumps(json_data, indent=2, ensure_ascii=False))


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


def get_id(name, resolver, is_an_id=None, return_none=False):
    if is_an_id is None:
        is_an_id = is_id(name)
    if is_an_id or not name:
        return name
    else:
        return resolver.resolve_name(name, return_none)


def system_exit(exit_process, apply_exit_code=True):
    exit_code = exit_process['code']
    if exit_process['message'] != '':
        print_color(exit_process['message'], 'green' if exit_code == 0 else 'red')
    if apply_exit_code or exit_code > 1:
        sys.exit(exit_process['code'])

