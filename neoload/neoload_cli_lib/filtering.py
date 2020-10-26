import re

last_filter_spec = None
last_input_params = None
def set_filter(filter_spec, input_params):
    global last_filter_spec, last_input_params
    last_filter_spec = filter_spec
    last_input_params = input_params
def clear_filter():
    global last_filter_spec, last_input_params
    last_filter_spec = None
    last_input_params = None

def stuff_current_filters(params):
    global last_filter_spec, last_input_params
    filter_spec = last_filter_spec
    input_params = last_input_params

    filters = {}
    if filter_spec is not None and len(filter_spec)>0:
        filters = parse_filter_spec(filter_spec)

    if input_params is not None and isinstance(input_params, list):
        for key in input_params:
            if key in filters: # move key/value from filter to query params
                params[key] = filters[key]
                del filters[key]

    return (params, filters)

def parse_filter_spec(filter_spec):
    ret = {}
    if filter_spec is not None:
        filter_parts = filter_spec.split("|" if "|" in filter_spec else ";")
        for part in filter_parts:
            subparts = part.split("=")
            key = subparts[0]
            value = "=".join(subparts[1:])
            ret[key] = value

    return ret

def remove_by_last_filter(all_entities):
    (params,filters) = stuff_current_filters({})
    return list(filter(lambda entity: entity_matches_all_filters(entity, filters), all_entities))

def entity_matches_all_filters(entity, filters):
    for key in filters.keys():
        if key in entity:
            find_re = filters[key].replace("*",".+")
            in_val = entity[key]
            if not re.search(find_re, in_val):
                return False
        else:
            return False
    return True
