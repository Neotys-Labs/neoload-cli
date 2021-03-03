import click
from neoload_cli_lib import cli_exception
import neoload_cli_lib.schema_validation as schema_validation
import os
from neoload_cli_lib.schema_validation import __default_schema_url

@click.command()
@click.option('--schema-url', help="The URL (or local path) to the as-code schema. By default, use the one on Github",
              metavar="URL", default=__default_schema_url, show_default=True)
@click.option('--refresh', is_flag=True, help="THIS OPTION IS NOW USELESS", hidden=True)
@click.option('--ssl-cert', default="", help="Path to SSL certificate or write False to disable certificate checking")
@click.argument('file')
def cli(file, refresh, schema_url, ssl_cert):
    """Verify that the yaml FILE matches the neoload as-code file format"""

    force_schema = os.environ.get('NLCLI_FORCE_SCHEMA')
    if force_schema is not None and len(force_schema) > 0:
        schema_url = force_schema

    path = os.path.abspath(file)
    try:
        if os.path.isdir(path):
            schema_validation.validate_yaml_dir(path, schema_url, ssl_cert)
            print('All yaml files underneath the path provided are valid.')
        else:
            schema_validation.validate_yaml(file, schema_url, ssl_cert)
            print('Yaml file is valid.')
    except Exception as err:
        raise cli_exception.CliException(str(err))
