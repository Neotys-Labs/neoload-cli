import click
from neoload_cli_lib.UserData import UserData

@click.group()
def cli():
    """Log out remove configuration file"""
    UserData.do_logout()

