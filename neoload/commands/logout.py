import click

from neoload_cli_lib import user_data


@click.command()
def cli():
    """Log out remove configuration file"""
    user_data.do_logout()
    print("logout successfully")
