import click
import neoload_cli_lib

@click.group()
def cli():
    """Log out remove configuration file"""
    neoload_cli_lib.UserData.do_logout()

