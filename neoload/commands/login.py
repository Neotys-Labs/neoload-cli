import sys
import click

from commands import workspaces
from neoload_cli_lib import user_data, tools, rest_crud


@click.command()
@click.option('--url', default="https://neoload-api.saas.neotys.com/", help="The URL of api ", metavar='URL')
@click.option('--no-write', is_flag=True, help="don't save login on application data")
@click.option('-l', '--local-conf', is_flag=True, help="save the application data on the current directory")
@click.option('--ssl-cert', default="", help="Path to SSL certificate or write False to disable certificate checking")
@click.option('--workspace', help="The Neoload Web workspace name or id. Optional. If not set, use the API v2 bound to the default workspace.")
@click.argument('token', required=False)
def cli(token, url, no_write, workspace, ssl_cert, local_conf):
    """Store your token and API url of NeoLoad Web. The token is read from stdin if none is set.
    The default API url is "https://neoload-api.saas.neotys.com/" """
    rest_crud.set_current_command()
    if not token:
        if sys.stdin.isatty():
            token = click.prompt("Enter your token", None, True)
        else:
            token = input()
    url = url.strip()
    if url[-1] != '/':
        url += '/'

    __user_data = user_data.do_login(token, url, no_write, ssl_cert, local_conf)

    if workspace is not None:
        if user_data.is_version_lower_than('2.5.0'):
            print("WARNING: The workspace option works only since Neoload Web 2.5.0. The specified workspace is ignored.")
        else:
            is_workspace_id = tools.is_mongodb_id(workspace)
            __id = tools.get_id(workspace, workspaces.__resolver, is_workspace_id)
            tools.use(__id, workspaces.meta_key, workspaces.__resolver)

    if sys.stdin.isatty():
        print(__user_data)
