import os
import sys
import click

from neoload_cli_lib import user_data, tools
import logging

@click.command()
def cli():
    """get status of NeoLoad cli Settings"""
    login = user_data.get_user_data(False)
    if login is None:
        print("No settings is stored. Please use \"neoload login\" to start.")
    else:
        print(login)

        logging.debug({
            "interactive_environment_variable": os.getenv(tools.__nl_interactive_env_var),
            "interactive_tty": sys.__stdin__.isatty(),
            "interactive_effective": tools.is_user_interactive()
        })
