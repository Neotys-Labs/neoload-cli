"""Turn the raw jsonschema errors of an as-code project into a short report: one entry per mistake.

A jsonschema error list is hard to read for a project made of steps that can each be one of ~20 kinds
(request, transaction, web_page, ...): the schema uses oneOf, and jsonschema reports "not valid under any of
the given schemas" with the failures of every alternative. Everything here is a pure function of the errors
and the project; nothing is printed, logged or modified.
"""
import re
from itertools import takewhile
from typing import NamedTuple, Tuple

import yaml

COLLECTIONS = {'user_paths': 'user_path', 'variables': 'variable', 'servers': 'server',
               'populations': 'population', 'scenarios': 'scenario', 'sla_profiles': 'sla_profile'}
STRUCTURAL_KEYS = set(COLLECTIONS) | {'steps', 'actions', 'init', 'end'}
VALUE_MAX_LENGTH = 160
STEP_NAME_MAX_LENGTH = 60
PATHS_SHOWN = 4
UNEXPECTED_KEYS = re.compile(r"^Unevaluated properties are not allowed \((.*) (?:was|were) unexpected\)$")


class Finding(NamedTuple):
    """One mistake at one place of the project."""
    path: Tuple
    message: str
    value: str   # the offending value, shortened. Empty when it would not help.
    steps: str   # the named steps leading to the mistake


# --- choosing the errors worth reporting ---------------------------------------------------------------

def depth(errors):
    return max(len(error.absolute_path) for error in errors)


def by_alternative(errors):
    """Group the errors of a oneOf/anyOf by the alternative that raised them."""
    groups = {}
    for error in errors:
        groups.setdefault(error.relative_schema_path[0], []).append(error)
    return list(groups.values())


def deepest_errors(error):
    """The errors that hold the real mistake behind an error.

    The alternative of a oneOf that fails deepest in the document is the one whose shape matched the most.
    If no alternative gets past the oneOf's own level, none was recognised: keep the oneOf error itself.
    """
    if not error.context:
        return [error]
    best = max(by_alternative(error.context), key=lambda errors: (depth(errors), -len(errors)))
    if depth(best) <= len(error.absolute_path):
        return [error]
    return [leaf for sub_error in best for leaf in deepest_errors(sub_error)]


def unexpected_keys(error):
    """The keys named by an "Unevaluated properties are not allowed" error, none for another error."""
    match = UNEXPECTED_KEYS.match(error.message)
    return [key.strip().strip("'") for key in match.group(1).split(',')] if match else []


def is_side_effect_of_invalid_value(error, error_paths):
    """A key whose value is invalid is also reported as unexpected: keep only the invalid value."""
    path = tuple(map(str, error.absolute_path))
    keys = unexpected_keys(error)
    return bool(keys) and all(any(other[:len(path) + 1] == path + (key,) for other in error_paths)
                              for key in keys)


def document_order(error):
    """Sort key putting steps[2] before steps[10]: list positions compare as numbers."""
    return [(0, part) if isinstance(part, int) else (1, str(part)) for part in error.absolute_path]


def real_errors(errors):
    leaves = [leaf for error in errors for leaf in deepest_errors(error)]
    error_paths = [tuple(map(str, leaf.absolute_path)) for leaf in leaves]
    return [leaf for leaf in leaves if not is_side_effect_of_invalid_value(leaf, error_paths)]


# --- describing one error --------------------------------------------------------------------------------

def shorten(text, max_length):
    return text if len(text) <= max_length else text[:max_length] + '...'


def show_value(value):
    one_line = yaml.dump(value, default_flow_style=True, width=10 ** 6).replace('\n...\n', '').strip()
    return shorten(one_line.replace('\n', ' '), VALUE_MAX_LENGTH)


def format_path(path):
    """user_paths[0].actions.steps[1]"""
    text = ''.join('[%s]' % part if isinstance(part, int) else '.' + str(part) for part in path)
    return text.lstrip('.') or '(root)'


def nodes_along(project, path):
    """(key before, key, node) for each element of the path that exists in the project."""
    node, key_before = project, None
    for key in path:
        try:
            node = node[key]
        except (KeyError, IndexError, TypeError):
            return
        yield key_before, key, node
        key_before = key


def step_label(key_before, key, node):
    """"transaction 'Login'", "user_path 'Main'", or None for a node that names nothing."""
    if not isinstance(node, dict):
        return None
    if isinstance(key, int) and key_before in COLLECTIONS:
        return "%s '%s'" % (COLLECTIONS[key_before], node.get('name', key))
    if isinstance(key, str) and key_before is not None and key not in STRUCTURAL_KEYS:
        name = node.get('url') if key == 'request' else node.get('name') or node.get('url')
        return "%s '%s'" % (key, shorten(str(name), STEP_NAME_MAX_LENGTH)) if name else key
    return None


def step_names(project, path):
    """user_path 'Main' > transaction 'Login' > request '/logon'"""
    labels = (step_label(*node) for node in nodes_along(project, path))
    return ' > '.join(label for label in labels if label)


def describe(error):
    """(message, value) to show for an error."""
    if error.validator in ('oneOf', 'anyOf'):   # no alternative recognised: do not dump the subtree
        if isinstance(error.instance, dict):
            return 'Unrecognised or invalid content, found the keys: ' + ', '.join(map(str, error.instance)), ''
        return 'Invalid value ' + show_value(error.instance), ''
    return error.message, show_value(error.instance)


def finding(error, project):
    path = tuple(error.absolute_path)
    message, value = describe(error)
    return Finding(path, message, value, step_names(project, path))


# --- grouping and rendering ------------------------------------------------------------------------------

def group_key(found):
    """The same mistake repeated on many steps is one finding: same message, about the same key."""
    keys = [part for part in found.path if not isinstance(part, int)]
    return (keys[-1] if keys else '', found.message)


def group(findings):
    groups = {}
    for found in findings:
        groups.setdefault(group_key(found), []).append(found)
    return list(groups.values())


def elide_shared_prefix(path, reference):
    """Replace the leading elements shared with the reference path by '...'; the last one always stays."""
    parts = path.split('.')
    shared = len(list(takewhile(lambda pair: pair[0] == pair[1], zip(parts[:-1], reference.split('.')))))
    return '...' + '.'.join(parts[shared:]) if shared else path


def also_at(paths):
    """"...steps[1].request, ...steps[2].request and 5 more" for the places after the first."""
    others = [elide_shared_prefix(path, paths[0]) for path in paths[1:PATHS_SHOWN]]
    more = len(paths) - PATHS_SHOWN
    return ', '.join(others) + (' and %d more' % more if more > 0 else '')


def render_group(findings):
    first = findings[0]
    paths = [format_path(found.path) for found in findings]
    lines = [first.message, '\tat: ' + paths[0]]
    if len(paths) > 1:
        lines.append('\talso at: ' + also_at(paths))
    if first.steps:
        lines.append('\tin: ' + first.steps)
    if first.value:
        lines.append('\tgot: ' + first.value)
    return '\n'.join(lines)


def summary(groups):
    places = sum(len(g) for g in groups)
    return '%d error(s)' % len(groups) + (' (%d places)' % places if places != len(groups) else '')


def format_errors(errors, project):
    """The report for the jsonschema errors of a project: a count, then one entry per mistake."""
    ordered = sorted(real_errors(errors), key=document_order)
    groups = group([finding(error, project) for error in ordered])
    return '\n'.join([summary(groups)] + [render_group(g) for g in groups])
