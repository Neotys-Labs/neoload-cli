import click
from click import ClickException
from neoload_cli_lib.SchemaValidation import SchemaValidation


@click.command()
@click.option('--schema-url', help="The URL of the as-code schema. By default, use the one on Github", metavar="URL",
              default="https://raw.githubusercontent.com/Neotys-Labs/neoload-cli/master/resources/as-code.latest.schema.json")
@click.argument('file')
def cli(file, schema_url):
    """Verify that the yaml FILE matches the neoload as-code file format"""
    try:
        SchemaValidation.validate_yaml(file, schema_url)
    except Exception as err:
        raise ClickException(str(err))
    print('Yaml file is valid.')
