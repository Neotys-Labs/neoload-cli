import click
import neoload_cli_lib.schema_validation as schema_validation

@click.command()
@click.option('-s', '--as-code-schema', default=None,
              help="NeoLoad as-code schema (URL or local path) to validate FILE against. "
                   "When omitted, download schemas/v<schemaVersion>/as-code.schema.json from neoload-models (v3). "
                   "If schemaVersion is absent, use schemas/v3.0/as-code.schema.json.",
              metavar="PATH|URL")
@click.option('--schema-url', 'schema_url', default=None, hidden=True,
              help="Deprecated alias for --as-code-schema, kept for backward compatibility.")
@click.option('--refresh', is_flag=True, help="THIS OPTION IS NOW USELESS", hidden=True)
@click.option('--ssl-cert', default="", help="Path to SSL certificate or write False to disable certificate checking")
@click.argument('file')
def cli(file, refresh, as_code_schema, schema_url, ssl_cert):
    """Verify that the yaml FILE matches the neoload as-code file format"""
    # -s/--as-code-schema (new) takes priority over --schema-url (deprecated alias)
    resolved_schema = as_code_schema or schema_url
    print(schema_validation.validate_path(file, resolved_schema, ssl_cert))
