import click
import neoload_cli_lib.schema_validation as schema_validation
from neoload_cli_lib.schema_validation import __default_schema_url

@click.command()
@click.option('--schema-url', help="The URL (or local path) to the as-code schema. By default, use the one on Github",
              metavar="URL", default=__default_schema_url, show_default=True)
@click.option('--refresh', is_flag=True, help="THIS OPTION IS NOW USELESS", hidden=True)
@click.option('--ssl-cert', default="", help="Path to SSL certificate or write False to disable certificate checking")
@click.argument('file')
def cli(file, refresh, schema_url, ssl_cert):
    """Verify that the yaml FILE matches the neoload as-code file format"""
    print(schema_validation.validate_path(file, schema_url, ssl_cert))
