import ast

import click

from neoload_cli_lib import config_global, rest_crud


@click.command()
@click.argument('command', type=click.Choice(['ls', 'set'], case_sensitive=False), required=True)
@click.argument('key_value', nargs=-1, required=False)
def cli(command, key_value):
    """View and set the user-defined properties. This properties is kept after logout. The format of KEY_VALUE: key1=value1 key2=value2. The empty value remove the key"""
    rest_crud.set_current_command()
    if command == 'set':
        for element in key_value:
            key, value = element.split('=')
            config_global.set_attr(key, treat_value(value))
    elif command == 'ls':
        print("config file: " + config_global.get_config_file() + "\n")
        for k, v in config_global.list_attr(key_value):
            print(k + " = " + str(v))


def treat_value(value):
    try:
        return ast.literal_eval(value or "None")
    except Exception:
        lower = value.lower()
        if lower in ['true', 'yes', 'y']:
            return True
        elif lower in ['false', 'no', 'n']:
            return False
        return str(value)
