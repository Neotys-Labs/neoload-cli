import click
from neoload_cli_lib import UserData

@click.command()
def cli():
    """Log out remove configuration file"""
    UserData.do_logout()
    print("logout successfully")


