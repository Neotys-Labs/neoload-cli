import click
from commands import test_settings
from neoload_cli_lib import user_data, tools, rest_crud, neoLoad_project


@click.command()
@click.argument("command", required=True, type=click.Choice(['up', 'upload', 'meta']))
@click.option("--path", "-p", type=click.Path(exists=True), default='.',
              help="path of the project folder, zip file or yaml as-code file. . is default value")
@click.argument("name_or_id", type=str, required=False)
def cli(command, name_or_id, path):
    """Upload and list scenario from settings"""
    if not name_or_id or name_or_id == "cur":
        name_or_id = user_data.get_meta(test_settings.meta_key)

    if not tools.is_id(name_or_id):
        name_or_id = test_settings.__resolver.resolve_name(name_or_id)

    if command[:2] == "up":
        upload(path, name_or_id)
    elif command == "meta":
        meta_data(name_or_id)
    user_data.set_meta(test_settings.meta_key, name_or_id)
    rest_crud.set_current_sub_command(command)


def upload(path, settings_id):
    #TODO: pre-validate with 'neoload validate' functionality, but..
    #TODO: provide a --skip-validation option
    neoLoad_project.upload_project(path, "v2/tests/" + settings_id + "/project")


def meta_data(setting_id):
    neoLoad_project.display_project(rest_crud.get_from_file_storage('v2/tests/' + setting_id + "/project"))
