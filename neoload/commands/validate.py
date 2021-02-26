import click
from neoload_cli_lib import cli_exception
import neoload_cli_lib.schema_validation as schema_validation
import os
from neoload_cli_lib.schema_validation import __default_schema_url

@click.command()
@click.option('--schema-url', help="The URL of the as-code schema. By default, use the one on Github", metavar="URL",
              default=__default_schema_url)
@click.option('--refresh', is_flag=True, help="this options update schema from the web")
@click.option('--ssl-cert', default="", help="Path to SSL certificate or write False to disable certificate checking")
@click.argument('file')
def cli(file, refresh, schema_url, ssl_cert):
    """Verify that the yaml FILE matches the neoload as-code file format"""

    path = os.path.abspath(file)
    try:
        if os.path.isdir(path):
            schema_validation.validate_yaml_dir(path, schema_url if refresh else None, ssl_cert)
            print('All yaml files underneath the path provided are valid.')
        else:
            schema_validation.validate_yaml(file, schema_url if refresh else None, ssl_cert)
            print('Yaml file is valid.')
    except Exception as err:
        raise cli_exception.CliException(str(err))
