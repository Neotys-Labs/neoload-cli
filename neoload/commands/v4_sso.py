import json
import click
from neoload_cli_lib import rest_crud, tools, cli_exception
from neoload_cli_lib.v4 import v4_endpoints


@click.command()
@click.argument('command', type=click.Choice([
    'config-get', 'config-create', 'config-put', 'config-patch', 'config-delete',
    'config-status',
    'saml-idp-get', 'saml-idp-put', 'saml-idp-delete',
    'saml-sp-metadata'
], case_sensitive=False), required=False)
@click.option('--file', 'input_file', type=click.File('r'), help='JSON body file (for config-create, config-put, config-patch, saml-idp-put)')
def cli(command, input_file):
    """
    config-get          # Get SSO configuration                                           .
    config-create       # Create SSO configuration (--file for JSON body)                 .
    config-put          # Replace SSO configuration (--file for JSON body)                .
    config-patch        # Update SSO configuration (--file for JSON body)                 .
    config-delete       # Delete SSO configuration                                        .
    config-status       # Get SSO configuration status                                    .
    saml-idp-get        # Get SAML identity provider metadata                             .
    saml-idp-put        # Set SAML identity provider metadata (--file for JSON body)      .
    saml-idp-delete     # Delete SAML identity provider metadata                          .
    saml-sp-metadata    # Get SAML service provider metadata                              .
    """
    rest_crud.set_current_command()
    if not command:
        print("command is mandatory. Please see neoload v4-sso --help")
        return
    rest_crud.set_current_sub_command(command)

    if command == 'config-get':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('sso', 'configuration')))
        return

    if command == 'config-create':
        body = _load_body(input_file)
        tools.print_json(rest_crud.post(v4_endpoints.v4_endpoint('sso', 'configuration'), body))
        return

    if command == 'config-put':
        body = _load_body(input_file)
        tools.print_json(rest_crud.put(v4_endpoints.v4_endpoint('sso', 'configuration'), body))
        return

    if command == 'config-patch':
        body = _load_body(input_file)
        tools.print_json(rest_crud.patch(v4_endpoints.v4_endpoint('sso', 'configuration'), body))
        return

    if command == 'config-delete':
        response = rest_crud.delete(v4_endpoints.v4_endpoint('sso', 'configuration'))
        if response.content:
            tools.print_json(response.json())
        else:
            print('SSO configuration deleted.')
        return

    if command == 'config-status':
        tools.print_json(rest_crud.get(v4_endpoints.v4_endpoint('sso', 'configuration', 'status')))
        return

    if command == 'saml-idp-get':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('saml2', 'identity-provider-metadata')))
        return

    if command == 'saml-idp-put':
        body = _load_body(input_file)
        tools.print_json(rest_crud.put(
            v4_endpoints.v4_endpoint('saml2', 'identity-provider-metadata'), body))
        return

    if command == 'saml-idp-delete':
        response = rest_crud.delete(
            v4_endpoints.v4_endpoint('saml2', 'identity-provider-metadata'))
        if response.content:
            tools.print_json(response.json())
        else:
            print('SAML identity provider metadata deleted.')
        return

    if command == 'saml-sp-metadata':
        tools.print_json(rest_crud.get(
            v4_endpoints.v4_endpoint('saml2', 'service-provider-metadata')))
        return


def _load_body(input_file):
    """Load JSON body from file, or return empty dict if no file provided."""
    if not input_file:
        return {}
    try:
        return json.load(input_file)
    except json.JSONDecodeError as err:
        raise cli_exception.CliException(
            '%s\nThis command requires valid JSON input.' % str(err))
