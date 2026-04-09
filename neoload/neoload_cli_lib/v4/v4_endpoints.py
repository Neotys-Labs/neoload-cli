from neoload_cli_lib import user_data, cli_exception


def v4_base():
    """Return the v4 API prefix string."""
    return 'v4'


def v4_endpoint(*segments):
    """Join any number of path segments after 'v4/'.

    Examples:
        v4_endpoint('tests') -> 'v4/tests'
        v4_endpoint('tests', test_id) -> 'v4/tests/{id}'
        v4_endpoint('tests', test_id, 'scenarios') -> 'v4/tests/{id}/scenarios'
    """
    return 'v4/' + '/'.join(str(s) for s in segments)


def v4_workspace_params():
    """Return {'workspaceId': id} dict for query parameters.

    Raises CliException if no workspace is stored. This is mandatory --
    all v4 workspace-scoped list operations require a workspace.
    """
    workspace_id = user_data.get_meta('workspace id')
    if workspace_id is None:
        raise cli_exception.CliException(
            "No workspace set. Please use 'neoload workspaces use <id>' first."
        )
    return {'workspaceId': workspace_id}


def v4_inject_workspace(data):
    """Return a copy of data dict with workspaceId added for request body injection.

    Raises CliException if no workspace is stored. This is mandatory --
    all v4 workspace-scoped create operations require a workspace in the body.
    """
    workspace_id = user_data.get_meta('workspace id')
    if workspace_id is None:
        raise cli_exception.CliException(
            "No workspace set. Please use 'neoload workspaces use <id>' first."
        )
    result = dict(data)
    result['workspaceId'] = workspace_id
    return result
