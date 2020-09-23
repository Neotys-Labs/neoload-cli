import click
from neoload_cli_lib import cli_exception
import neoload_cli_lib.schema_validation as schema_validation


@click.command()
@click.option('--schema-url', help="The URL of the as-code schema. By default, use the one on Github", metavar="URL",
              default="https://raw.githubusercontent.com/Neotys-Labs/neoload-models/v3/neoload-project/src/main/resources/as-code.latest.schema.json")
@click.option('--refresh', is_flag=True, help="this options update schema from the web")
@click.option('--ssl-cert', default="", help="Path to SSL certificate or write False to disable certificate checking")
@click.argument('file')
def cli(file, refresh, schema_url, ssl_cert):
    """Verify that the yaml FILE matches the neoload as-code file format"""
    try:
        schema_validation.validate_yaml(file, schema_url if refresh else None, ssl_cert)
    except Exception as err:
        raise cli_exception.CliException(str(err))
    print('Yaml file is valid.')
