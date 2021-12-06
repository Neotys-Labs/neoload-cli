import json
import os
import re
import sys

import click
from click import ClickException
from termcolor import cprint

from neoload_cli_lib import rest_crud, user_data, config_global, filtering

from version import __version__

__regex_id = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
__regex_mongodb_id = re.compile('[a-f\\d]{24}', re.IGNORECASE)
__true_values = ["true", "yes", "y", "1"]
__false_values = ["false", "no", "n", "0"]
__nl_interactive_env_var = 'NL_INTERACTIVE'
__ci_env_var_signatures = {
    "jenkins": ["JENKINS_URL"],  # https://wiki.jenkins.io/display/JENKINS/Building+a+software+project
    "travis": ["TRAVIS"],  # https://docs.travis-ci.com/user/environment-variables/#default-environment-variables
    "bamboo": ["bamboo_buildNumber"],  # https://stackoverflow.com/a/44330836
    # https://docs.aws.amazon.com/codebuild/latest/userguide/build-env-ref-env-vars.html
    "codebuild": ["CODEBUILD_BUILD_ARN"],
    # https://docs.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops&tabs=yaml
    "azure": ["AGENT_TOOLSDIRECTORY"],
    "gitlab": ["CI_PROJECT_ID"],  # https://docs.gitlab.com/ee/ci/variables/predefined_variables.html
    "teamcity": ["TEAMCITY_VERSION"],  # https://www.jetbrains.com/help/teamcity/predefined-build-parameters.html
    "circleci": ["CIRCLECI"],  # https://circleci.com/docs/2.0/env-vars/#built-in-environment-variables
    # https://cloud.google.com/cloud-build/docs/configuring-builds/substitute-variable-values
    "gcloudbuild": ["BUILD_ID"],
    "generic_ci": ["CONTINUOUS_INTEGRATION", "CI"],  # travis, circleci, and others
}

__batch = False


def compute_version():
    if __version__ is not None:
        return __version__
    try:
        return os.popen('git describe --tags --dirty').read().strip()
    except (TypeError, ValueError):
        return "dev"


def __is_color_terminal():
    if not sys.stdout.isatty():
        return False
    if os.getenv('COLORTERM'):
        return True
    if os.getenv('TERM_PROGRAM') in {'iTerm.app', 'Hyper', 'Apple_Terminal'}:
        return True
    if os.getenv('TERM') in {'screen-256', 'screen-256color', 'xterm-256', 'xterm-256color', 'color', 'cygwin'}:
        return True
    return False


__is_color_term = __is_color_terminal()


def is_color_terminal():
    return __is_color_term


def print_color(text, color=None, on_color=None, attrs=None, **kwargs):
    if __is_color_term:
        cprint(text, color, on_color, attrs, **kwargs)
    else:
        print(text)


def set_batch(batch: bool):
    global __batch
    __batch = batch


def is_batch():
    return __batch


def is_mongodb_id(chain: str):
    if chain:
        return __regex_mongodb_id.match(chain)
    return False


def is_id(chain: str):
    if chain:
        return __regex_id.match(chain)
    return False


def confirm(message: str, quit_option=False):
    if sys.stdin.isatty() and not __batch:
        choice = ['y', 'n']
        if quit_option:
            choice.append('q')
        response = click.prompt(message, default='n', type=click.Choice(choice, case_sensitive=False), err=True)
        if quit_option and response == 'q':
            quit(0)
        return response == 'y'
    return True


def get_named_or_id(name, is_id_, resolver):
    endpoint = resolver.get_endpoint()
    if not is_id_:
        json_or_id = resolver.resolve_name_or_json(name)
        if type(json_or_id) is not str:
            return json_or_id
        else:
            name = json_or_id

    return rest_crud.get(endpoint + "/" + name)


def ls(name, is_id_, resolver, filter_spec=None, allowed_api_query_params=None):
    endpoint = resolver.get_endpoint()
    if name:
        get_id_and_print_json(get_named_or_id(name, is_id_, resolver))
    else:
        (api_query_params, cli_params) = filtering.parse_filters(filter_spec, allowed_api_query_params)
        all_entities = rest_crud.get_with_pagination(endpoint, api_query_params=api_query_params)
        print_json(filtering.remove_by_filter(all_entities, cli_params))


def delete(endpoint, id_data, kind):
    if confirm("You will delete a " + kind + " with id: " + id_data + " Are your sure ?"):
        return rest_crud.delete(endpoint + "/" + id_data)
    raise click.Abort


def use(name, meta_key, resolver):
    """Set the default test settings"""
    if name:
        user_data.set_meta(meta_key, name)
    else:
        default_id = user_data.get_meta(meta_key)
        for (name, settings_id) in resolver.get_map().items():
            prefix = '* ' if default_id == settings_id else '  '
            print(prefix + name + "\t: " + settings_id)


def print_json(json_data):
    print(json.dumps(json_data, indent=2, ensure_ascii=False))


def get_id_and_print_json(json_data: json):
    print_json(json_data)
    if 'id' not in json_data:
        raise ClickException('No uui returned. Operation may have failed !')
    return json_data['id']


def is_integer(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


def get_id(name, resolver, is_an_id=None, return_none=False):
    if is_an_id is None:
        is_an_id = is_id(name)
    if is_an_id or not name:
        return name
    else:
        return resolver.resolve_name(name, return_none)


def system_exit(exit_process, apply_exit_code=True):
    exit_code = exit_process['code']
    if exit_process['message'] != '':
        print_color(exit_process['message'], 'green' if exit_code == 0 else 'red')
    if apply_exit_code or exit_code > 1:
        sys.exit(exit_process['code'])


def get_boolean_value_from_env(env_var, default=False):
    return os.getenv(env_var, str(default)).lower().strip() in __true_values

def string_to_bool_json(str):
    if str in __true_values:
        return True
    if str in __false_values:
        return False
    return None

def get_true_values():
    return __true_values

def get_false_values():
    return __false_values

def is_user_interactive():
    return get_boolean_value_from_env(__nl_interactive_env_var, False) or config_global.get_attr("interactive", False)


def are_any_ci_env_vars_active():
    for ci in __ci_env_var_signatures:
        for env_var in __ci_env_var_signatures[ci]:
            if os.getenv(env_var, 'false').lower().strip() not in __false_values:
                return True
    return False


def ssl_cert_to_verify(ssl_cert):
    if not ssl_cert:
        return True
    if ssl_cert == 'False':
        return False
    return ssl_cert
