import click


@click.command()
@click.argument("command", required=True, type=click.Choice(['up', 'upload', 'meta', 'ls-scenario']))
@click.option("--path", "-p", type=click.Path(exists=True), help="path of project is pwd by default")
@click.argument("name_or_id", type=str)
def cli(command, name_or_id, path):
    """Upload and list scenario from settings"""
    pass


def upload(path, settings_id):
    pass


def meta_data(setting_id):
    pass


def scenario(settings_id):
    pass
