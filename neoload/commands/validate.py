import click
import neoload_cli_lib.schema_validation as schema_validation
from neoload_cli_lib.schema_validation import __default_schema_url

@click.command()
@click.option('-s', '--as-code-schema', default=None,
              help="NeoLoad as-code schema (URL or local path) to validate FILE against. "
                   "Defaults to the schema published for this release on Github.",
              metavar="PATH|URL")
@click.option('--schema-url', 'schema_url', default=None, hidden=True,
              help="Deprecated alias for --as-code-schema, kept for backward compatibility.")
@click.option('--refresh', is_flag=True, help="THIS OPTION IS NOW USELESS", hidden=True)
@click.option('--ssl-cert', default="", help="Path to SSL certificate or write False to disable certificate checking")
@click.argument('file')
def cli(file, refresh, as_code_schema, schema_url, ssl_cert):
    """Verify that the yaml FILE matches the neoload as-code file format"""
    # -s/--as-code-schema (new) takes priority over --schema-url (deprecated alias)
    resolved_schema = as_code_schema or schema_url or __default_schema_url
    print(schema_validation.validate_path(file, resolved_schema, ssl_cert))
