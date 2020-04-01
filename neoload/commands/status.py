import click

from neoload_cli_lib import UserData

@click.command()
def cli():
    """get status of NeoLoad cli Settings"""
    login = UserData.get_login(False)
    if login is None:
        print("No settings is stored. Please use \"neoload login\" to start.")
    else:
        print(login)
    pass
