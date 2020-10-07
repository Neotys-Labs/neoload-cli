import click
from commands import test_settings
from neoload_cli_lib import user_data, tools, rest_crud, neoLoad_project


@click.command()
@click.argument("command", required=True, type=click.Choice(['up', 'upload', 'meta']))
@click.option("--path", "-p", type=click.Path(exists=True), default='.',
              help="path of project folder, zip or yml file. . is default value")
@click.option("--display-progress/--just-json", is_flag=True, required=False, default=True,
              help=("Suppress the real-time progress when files is above " + str(neoLoad_project.MAX_FILE_MB_BEFORE_PROGRESS) + "MB") )
@click.argument("name_or_id", type=str, required=False)
def cli(command, name_or_id, path, display_progress):
    """Upload and list scenario from settings"""
    if not name_or_id or name_or_id == "cur":
        name_or_id = user_data.get_meta(test_settings.meta_key)

    if not tools.is_id(name_or_id):
        name_or_id = test_settings.__resolver.resolve_name(name_or_id)

    if not tools.is_user_interactive():
        display_progress = False  # just JSON, no rewriting of stdin allowed in non interactive mode

    if command[:2] == "up":
        upload(path, name_or_id, display_progress)
    elif command == "meta":
        meta_data(name_or_id)
    user_data.set_meta(test_settings.meta_key, name_or_id)
    rest_crud.set_current_sub_command(command)


#TODO: pre-validate with 'neoload validate' functionality, but..
#TODO: provide a --skip-validation option
#TODO: spider through all YAML (as-code files)
#TODO: fix validate to recurse through all includes; create unique file list map (avoid recursive references)

def upload(path, settings_id, display_progress):
    neoLoad_project.upload_project(path, get_endpoint(settings_id), display_progress)


def meta_data(setting_id):
    neoLoad_project.display_project(rest_crud.get_from_file_storage(get_endpoint(setting_id)))


def get_endpoint(settings_id: str):
    return rest_crud.base_endpoint_with_workspace() + '/tests/' + settings_id + "/project"
