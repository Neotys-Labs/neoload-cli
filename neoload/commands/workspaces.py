import click
from neoload_cli_lib import rest_crud, tools, user_data
from neoload_cli_lib.name_resolver import Resolver


__endpoint = "/workspaces"
meta_key = 'workspace id'
__resolver = Resolver(__endpoint, rest_crud.base_endpoint, meta_key)


@click.command()
@click.argument('command', type=click.Choice(['ls', 'use'], case_sensitive=False), required=False)
@click.argument("name_or_id", type=str, required=False)
def cli(command, name_or_id):
    """
    ls     # Lists workspaces                                                .
    use    # Remember the workspace you want to work on                      .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload workspaces --help")
        return
    if user_data.is_version_lower_than('2.5.0'):
        print("ERROR: This commands works only since Neoload Web 2.5.0")
        return
    rest_crud.set_current_sub_command(command)
    if name_or_id == "cur":
        name_or_id = user_data.get_meta(meta_key)
    is_id = tools.is_mongodb_id(name_or_id)
    # avoid to make two requests if we have not id.
    if command == "ls":
        # The endpoint GET /workspaces/{workspaceId} is not yet implemented
        ws_filter = None
        if name_or_id is not None: ws_filter = "id={}".format(name_or_id)
        tools.ls(None, True, __resolver, ws_filter)
        return

    __id = tools.get_id(name_or_id, __resolver, is_id)

    if command == "use":
        tools.use(__id, meta_key, __resolver)
