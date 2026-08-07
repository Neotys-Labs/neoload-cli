import os
from pathlib import Path

import click

from neoload_cli_lib import cli_exception

__template_namespace = 'resources.templates'
__template_filename = 'default.yaml'
__project_yaml_name = 'default.yaml'


def _read_template() -> str:
    try:
        import importlib.resources as pkg_resources
    except ImportError:
        import importlib_resources as pkg_resources

    if hasattr(pkg_resources, 'files'):
        return pkg_resources.files(__template_namespace).joinpath(__template_filename).read_text(encoding='utf-8')
    return pkg_resources.read_text(__template_namespace, __template_filename, encoding='utf-8')


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

    project_dir = Path(project_name)
    if project_dir.exists():
        raise cli_exception.CliException(
            f"Cannot create project '{project_name}': path already exists."
        )

    try:
        template = _read_template()
        project_dir.mkdir(parents=False)
        yaml_path = project_dir / __project_yaml_name
        yaml_path.write_text(template, encoding='utf-8')
    except OSError as err:
        raise cli_exception.CliException(f"Failed to create project '{project_name}': {err}") from err

    print(f"Project '{project_name}' created successfully.")
    print(f"  {os.path.join(project_name, __project_yaml_name)}")
    print()
    print("Next step: verify your project with CheckVU:")
    print(f"  neoload checkvu {os.path.join(project_name, __project_yaml_name)}")
