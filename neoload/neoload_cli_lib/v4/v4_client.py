from neoload_cli_lib import rest_crud
from neoload_cli_lib.v4 import v4_endpoints


def v4_list(*path_segments, params=None):
    """Auto-paginating list for workspace-scoped v4 resources.

    Paginates using pageNumber/pageSize (NOT limit/offset).
    Auto-injects workspaceId as query param. Raises CliException if no workspace set.
    Returns a flat Python list (items unwrapped from page envelopes).

    Args:
        *path_segments: Variable path segments passed to v4_endpoint().
        params: Optional dict of additional query parameters (e.g. filters).
    """
    endpoint = v4_endpoints.v4_endpoint(*path_segments)
    workspace_params = v4_endpoints.v4_workspace_params()  # raises CliException if no workspace

    page_number = 0
    page_size = 200
    all_items = []

    while True:
        query_params = {**workspace_params, 'pageNumber': page_number, 'pageSize': page_size}
        if params:
            query_params.update(params)
        response = rest_crud.get(endpoint, query_params)
        items = response.get('items', [])
        all_items.extend(items)
        total = response.get('total', 0)
        if len(all_items) >= total or not items:
            break
        page_number += 1

    return all_items


def v4_get(*path_segments):
    """GET a single v4 resource by path.

    No workspace injection -- workspace is not needed for by-ID lookups.
    Returns response.json() dict.
    """
    return rest_crud.get(v4_endpoints.v4_endpoint(*path_segments))


def v4_create(*path_segments, data):
    """POST to create a v4 resource.

    Auto-injects workspaceId into request body. Raises CliException if no workspace set.
    data must be passed as keyword argument.
    Returns response.json() dict.
    """
    injected = v4_endpoints.v4_inject_workspace(data)  # raises CliException if no workspace
    return rest_crud.post(v4_endpoints.v4_endpoint(*path_segments), injected)


def v4_update(*path_segments, data):
    """PATCH a v4 resource.

    No workspace injection -- workspace is not needed for by-ID updates.
    data must be passed as keyword argument.
    Returns response.json() dict.
    """
    return rest_crud.patch(v4_endpoints.v4_endpoint(*path_segments), data)


def v4_replace(*path_segments, data):
    """PUT (full replace) a v4 resource.

    No workspace injection.
    data must be passed as keyword argument.
    Returns response.json() dict.
    """
    return rest_crud.put(v4_endpoints.v4_endpoint(*path_segments), data)


def v4_delete(*path_segments):
    """DELETE a v4 resource.

    No workspace injection.
    Returns response.json() dict, or None if the response body is empty
    (e.g. HTTP 202 Accepted or 204 No Content).
    """
    response = rest_crud.delete(v4_endpoints.v4_endpoint(*path_segments))
    # rest_crud.delete returns raw requests.Response (not .json())
    if response.status_code == 204 or not response.content:
        return None
    return response.json()
