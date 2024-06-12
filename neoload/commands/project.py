import os
import zipfile

import click

from commands import test_settings
from neoload_cli_lib import user_data, tools, rest_crud, neoLoad_project


@click.command()
@click.argument("command", required=True, type=click.Choice(['up', 'upload', 'meta']))
@click.option("--path", "-p", type=click.Path(exists=True), default=os.getcwd(),
              help="path of project folder, zip or yml file. . is default value")
@click.option("--save", "-s", type=click.Path(exists=False),
              help="Path to a (non-existent) file ending in .zip to preserve what was uploaded")
@click.argument("name_or_id", type=str, required=False)
def cli(command, name_or_id, path, save):
    """Upload and list scenario from settings"""
    rest_crud.set_current_command()
    if not name_or_id or name_or_id == "cur":
        name_or_id = user_data.get_meta(test_settings.meta_key)

    if not tools.is_id(name_or_id):
        name_or_id = test_settings.__resolver.resolve_name(name_or_id)

    if command[:2] == "up":
        upload(path, name_or_id, save)
    elif command == "meta":
        meta_data(name_or_id)
    user_data.set_meta(test_settings.meta_key, name_or_id)
    rest_crud.set_current_sub_command(command)


#TODO: pre-validate with 'neoload validate' functionality, but..
#TODO: provide a --skip-validation option
#TODO: spider through all YAML (as-code files)
#TODO: fix validate to recurse through all includes; create unique file list map (avoid recursive references)


def extract_nlp_from_zip(zip_path, extract_to='.'):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            if file.endswith('.nlp'):
                zip_ref.extract(file, extract_to)
                return os.path.join(extract_to, file)


def upload(path, settings_id, endpoint):
    if path.endswith('.zip'):
        nlp_file_path = extract_nlp_from_zip(path)
        if not nlp_file_path:
            print(f"Error: No .nlp file found in the zip archive {path}.")
    else:
        nlp_file_found = False
        nlp_file_path = None

        for root, dirs, files in os.walk(path):
            for file in files:
                print(f"Inspecting file: {file}")
                if file.endswith(".nlp"):
                    nlp_file_path = os.path.join(root, file)
                    nlp_file_found = True
                    break
            if nlp_file_found:
                break

        if not nlp_file_found:
            print(f"Error: No .nlp file found in the directory {path}.")

    if not os.path.exists(nlp_file_path):
        print(f"Error: The file {nlp_file_path} does not exist.")

    with open(nlp_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if 'project.password.hash=' in line:
                val = line.split('project.password.hash=')[1].strip()
                endpoint = get_endpoint(settings_id)
                if val:
                    print("Your project has a password, please go here to enter your password: " + "https://neoload.saas.neotys.com/#!test-settings/" + settings_id)
                    neoLoad_project.upload_project(path, endpoint)
                else:
                    neoLoad_project.upload_project(path, endpoint)


def meta_data(setting_id):
    neoLoad_project.display_project(rest_crud.get_from_file_storage(get_endpoint(setting_id)))


def get_endpoint(settings_id: str):
    return rest_crud.base_endpoint_with_workspace() + '/tests/' + settings_id + "/project"
