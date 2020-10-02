import click

from neoload_cli_lib import user_data


@click.command()
def cli():
    """get status of NeoLoad cli Settings"""
    login = user_data.get_user_data(False)
    if login is None:
        print("No settings is stored. Please use \"neoload login\" to start.")
    else:
        print(login)
