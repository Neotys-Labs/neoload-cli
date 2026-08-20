import os
import zipfile
import click
import urllib.parse as urlparse
from commands import test_settings
from pathlib import Path
from neoload_cli_lib import user_data, tools, rest_crud, neoLoad_project, cli_exception, resources

__template_namespace = 'resources.templates'
__template_filename = 'default.yaml'
__project_yaml_name = 'default.yaml'


@click.command()
@click.argument("command", required=True, type=click.Choice(['create', 'up', 'upload', 'meta']))
@click.option("--path", "-p", type=click.Path(exists=True), default=os.getcwd(),
              help="Path of project folder, zip or yml file. . is default value")
@click.option("--save", "-s", type=click.Path(exists=False),
              help="Path to a (non-existent) file ending in .zip to preserve what was uploaded")
@click.argument("name_or_id", type=str, required=False)
def cli(command, name_or_id, path, save):
    """
    create # Create a local as-code project folder from the demo yaml template.
    upload # Upload a project to NeoLoad Web test settings (alias: up)        .
    meta   # Display project metadata from the current test settings          .
    """
    if command == "create":
        create_local_project(name_or_id)
        return

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

def has_password_in_zip_project(zip_path) -> bool:
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        for file_name in zip_file.namelist():
            if file_name.endswith('.nlp'):
                with zip_file.open(file_name, 'r') as nlp_file:
                    return has_password_in_nlp(nlp_file)
    return False


def has_password_in_folder_project(folder_path) -> bool:
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".nlp"):
                with open(Path(root) / file, 'rb') as nlp_file:
                    return has_password_in_nlp(nlp_file)
    return False


def has_password_in_nlp(nlp_file) -> bool:
    for line in nlp_file:
        if b'project.password.hash=' in line:
            return True
    return False


#TODO: pre-validate with 'neoload validate' functionality, but..
#TODO: provide a --skip-validation option
#TODO: spider through all YAML (as-code files)
#TODO: fix validate to recurse through all includes; create unique file list map (avoid recursive references)

def upload(path, settings_id, save):
    path = Path(path)
    has_password = has_password_in_zip_project(path) if path.suffix == '.zip' else has_password_in_folder_project(path)
    if has_password:
        print("Your project has a password, please make sure your password is set in the test: " +
              urlparse.urljoin(user_data.get_user_data().get_frontend_url(), "/#!test-settings/" + settings_id))

    # Always call the upload_project method
    neoLoad_project.upload_project(path, get_endpoint(settings_id), save)


def meta_data(setting_id):
    neoLoad_project.display_project(rest_crud.get_from_file_storage(get_endpoint(setting_id)))


def get_endpoint(settings_id: str):
    return rest_crud.base_endpoint_with_workspace() + '/tests/' + settings_id + "/project"


def create_local_project(project_name):
    if project_name is None:
        raise cli_exception.CliException("Missing project name. Usage: neoload project create <project-name>")
    project_name = project_name.strip()
    if not project_name or project_name in ('.', '..'):
        raise cli_exception.CliException(f"Invalid project name: '{project_name}'.")
    if os.path.sep in project_name or (os.path.altsep and os.path.altsep in project_name):
        raise cli_exception.CliException(
            f"Invalid project name: '{project_name}'. Use a single folder name, not a path."
        )

    if os.path.exists(project_name):
        raise cli_exception.CliException(
            f"Cannot create project '{project_name}': path already exists."
        )

    yaml_path = os.path.join(project_name, __project_yaml_name)
    try:
        template = resources.get_resource_as_string(__template_namespace, __template_filename)
        os.mkdir(project_name)
        with open(yaml_path, 'w', encoding='utf-8') as yaml_file:
            yaml_file.write(template)
    except OSError as err:
        raise cli_exception.CliException(f"Failed to create project '{project_name}': {err}") from err

    print(f"Project '{project_name}' created successfully.")
    print(f"  {yaml_path}")
    print()
    print("Next step: verify your project with CheckVU:")
    print(f"  neoload checkvu {yaml_path}")
