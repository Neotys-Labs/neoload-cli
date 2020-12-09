import click
from commands import test_settings
from neoload_cli_lib import user_data, tools, rest_crud, neoLoad_project
import os

@click.command()
@click.argument("command", required=True, type=click.Choice(['up', 'upload', 'meta']))
@click.option("--path", "-p", type=click.Path(exists=True), default='.',
              help="path of project folder, zip or yml file. . is default value")
@click.option("--save", "-s", type=click.Path(exists=False),
              help="Path to a (non-existent) file ending in .zip to preserve what was uploaded")
@click.argument("name_or_id", type=str, required=False)
def cli(command, name_or_id, path, save):
    """Upload and list scenario from settings"""
    if not name_or_id or name_or_id == "cur":
        name_or_id = user_data.get_meta(test_settings.meta_key)

    if not tools.is_id(name_or_id):
        name_or_id = test_settings.__resolver.resolve_name(name_or_id)

    if command[:2] == "up":
        if save is not None:
            save = os.path.abspath(save)
            if not save.endswith(".zip"):
                tools.system_exit({'code':1,'message':'If you specify a --save file, it must end with .zip'})
                return
            if os.path.exists(save):
                tools.system_exit({'code':1,'message':"The --save file '{}' already exists! If you specify a --save file, it must not exist first. We wouldn't want to accidentally overwrite things, would we?".format(save)})
                return
        upload(path, name_or_id, save)
    elif command == "meta":
        meta_data(name_or_id)
    user_data.set_meta(test_settings.meta_key, name_or_id)
    rest_crud.set_current_sub_command(command)


#TODO: pre-validate with 'neoload validate' functionality, but..
#TODO: provide a --skip-validation option
#TODO: spider through all YAML (as-code files)
#TODO: fix validate to recurse through all includes; create unique file list map (avoid recursive references)

def upload(path, settings_id, save):
    neoLoad_project.upload_project(path, get_endpoint(settings_id), save=save)


def meta_data(setting_id):
    neoLoad_project.display_project(rest_crud.get_from_file_storage(get_endpoint(setting_id)))


def get_endpoint(settings_id: str):
    return rest_crud.base_endpoint_with_workspace() + '/tests/' + settings_id + "/project"
