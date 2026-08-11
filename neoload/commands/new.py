import os

import click

from neoload_cli_lib import cli_exception, resources

__template_namespace = 'resources.templates'
__template_filename = 'default.yaml'
__project_yaml_name = 'default.yaml'


@click.command('new')
@click.argument('project_name')
def cli(project_name):
    """Create a new as-code PROJECT_NAME folder with a demo yaml project."""
    if not project_name or project_name.strip() != project_name or project_name in ('.', '..'):
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
