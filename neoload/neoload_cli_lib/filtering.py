import re

last_filter_spec = None
last_allowed_api_query_params = None
def set_filter(filter_spec, allowed_api_query_params):
    global last_filter_spec, last_allowed_api_query_params
    last_filter_spec = filter_spec
    last_allowed_api_query_params = allowed_api_query_params
def clear_filter():
    global last_filter_spec, last_allowed_api_query_params
    last_filter_spec = None
    last_allowed_api_query_params = None

def parse_filters(params):
    global last_filter_spec, last_allowed_api_query_params
    filter_spec = last_filter_spec
    allowed_api_query_params = last_allowed_api_query_params

    filters = parse_filter_spec(filter_spec)

    return (allowed_api_query_params, filters)

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

def remove_by_last_filter(all_entities):
    (allowed_api_query_params,filters) = parse_filters({})
    return list(filter(lambda entity,fils=filters: entity_matches_all_filters(entity, fils), all_entities))

def entity_matches_all_filters(entity, filters):
    for key in filters.keys():
        if key in entity:
            find_re = filters[key]
            in_val = entity[key]
            if not re.search(find_re, in_val):
                return False
        else:
            return False
    return True
