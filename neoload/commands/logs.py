import click
import time
from neoload_cli_lib import logs_tools, rest_crud
from commands import test_results



@click.command()
@click.argument('name', type=str)
def cli(name):
    """get logs url of a test result managed by NeoLoad Web"""
    workspace = rest_crud.get_workspace()
    if workspace is None:
        print("You have not defined a workspace please use: neoload workspaces use 'your workspace'")
        return
    results_id = test_results.get_id_by_name_or_id(name)
    displayed_lines = []
    logs_tools.display_logs(displayed_lines, results_id)



