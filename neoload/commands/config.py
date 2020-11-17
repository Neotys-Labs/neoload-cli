import ast

import click

from neoload_cli_lib import config_global


@click.command()
@click.argument('command', type=click.Choice(['ls', 'set'], case_sensitive=False), required=True)
@click.argument('key_values', required=False)
def cli(command, key_values):
    if command == 'set':
        key, value = key_values.split('=')

        config_global.set_attr(key, treat_value(value))
    elif command == 'ls':
        print("config file: " + config_global.get_config_file() + "\n")
        for k, v in config_global.list_attr(key_values):
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
