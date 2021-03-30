import re

def parse_filters(filter_spec, allowed_api_query_params):
    """
    Reads the filter_spec and return the filters that can be applied with public API
    and filters that must be applied by the CLI on the result list
    """
    cli_params = parse_filter_spec(filter_spec)
    api_query_params = {}
    if allowed_api_query_params is not None and isinstance(allowed_api_query_params, list):
        for key in allowed_api_query_params:
            if key in cli_params:  # move key/value from filter to query params
                api_query_params[key] = cli_params[key]
                del cli_params[key]

    return api_query_params, cli_params


def parse_filter_spec(filter_spec):
    ret = {}

    if filter_spec is not None and len(filter_spec)>0:
        filter_parts = filter_spec.split("|" if "|" in filter_spec else ";")
        for part in filter_parts:
            subparts = part.split("=")
            key = subparts[0]
            value = "=".join(subparts[1:])
            ret[key] = value

    return ret


def remove_by_filter(all_entities, cli_params):
    """
    Remove all elements from the list 'all_entities' that don't match all the filters 'cli_params'
    """
    return list(filter(lambda entity: entity_matches_all_filters(entity, cli_params), all_entities))


def entity_matches_all_filters(entity, filters):
    for key in filters.keys():
        if key in entity:
            find_re = filters[key] # filter value is always a string from shell arguments
            in_val = str(entity[key]) # value from API entities might not always be string
            if not re.search(find_re, in_val):
                return False
        else:
            return False
    return True
