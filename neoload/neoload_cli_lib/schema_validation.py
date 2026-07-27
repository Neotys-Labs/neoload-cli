import json
from json import JSONDecodeError

import jsonschema
import requests
import yaml
from yaml.scanner import ScannerError

from neoload_cli_lib import cli_exception, bad_as_code_exception
from neoload_cli_lib.user_data import update_schema, get_yaml_schema, get_yaml_schema_etag, tools

import logging
import hashlib
import os
import  gitignorefile
from neoload_cli_lib.neoLoad_project import is_not_to_be_included

YAML_NOT_CONFIRM_MESSAGE = "YAML does not confirm to NeoLoad DSL schema."
__default_schema_url = "https://raw.githubusercontent.com/Neotys-Labs/neoload-models/v3/neoload-project/src/main/resources/as-code.latest.schema.json"

# Array-valued top-level as-code properties that get concatenated when merging
# several project files together (mirrors neoload-legacy's
# ConfigurationManager.mergeAsCodeProject, which does the same plain
# concatenation for a resolved "includes:" tree).
_MERGED_ARRAY_FIELDS = ['sla_profiles', 'variables', 'servers', 'user_paths', 'populations', 'scenarios']


def parse_yaml_file(file_path):
    try:
        yaml_content = open(file_path)
    except Exception as err:
        raise cli_exception.CliException('Unable to open file %s:\n%s' % (file_path, str(err)))

    try:
        yaml_as_object = yaml.load(yaml_content, yaml.FullLoader)
        if yaml_as_object is None:
            raise cli_exception.CliException('Empty file: ' + str(file_path))
    except ScannerError as err:
        raise cli_exception.CliException('This is not a valid yaml file [{}] :\n{}'.format(file_path, err))

    return yaml_as_object


def merge_projects(projects):
    merged = {}
    for field in _MERGED_ARRAY_FIELDS:
        items = [item for project in projects for item in project.get(field, [])]
        if items:
            merged[field] = items

    project_settings = {}
    for project in projects:
        project_settings.update(project.get('project_settings', {}))
    if project_settings:
        merged['project_settings'] = project_settings

    for project in projects:
        if project.get('name'):
            merged['name'] = project['name']

    return merged


def resolve_includes(entry_file_path, project_root=None, _visited=None):
    """Recursively resolve "includes:" starting from entry_file_path, mirroring
    neoload-legacy's ConfigurationManager.parseAsCodeFile: include paths are
    resolved relative to project_root (not to the including file's own
    directory), only "yaml"/"yml"/"json" files are accepted, and a file
    currently being resolved on the same branch cannot be included again
    (infinite loop detection). Returns an ordered list of parsed dicts
    (includes first, entry file last) ready for merge_projects()."""
    entry_file_path = os.path.abspath(entry_file_path)
    if project_root is None:
        project_root = os.path.dirname(entry_file_path)
    if _visited is None:
        _visited = set()

    if entry_file_path in _visited:
        raise cli_exception.CliException('Infinite loop detected in includes for as code file: %s' % entry_file_path)
    _visited = _visited | {entry_file_path}

    doc = parse_yaml_file(entry_file_path)
    resolved = []
    for include in doc.get('includes', []):
        include_path = include if os.path.isabs(include) else os.path.join(project_root, include)
        if not include_path.lower().endswith(('.yaml', '.yml', '.json')):
            raise cli_exception.CliException(
                "The 'includes' field accepts only the following file extensions: 'yaml', 'yml' or 'json': %s" % include_path)
        if not os.path.exists(include_path):
            raise cli_exception.CliException('As code file not found: %s' % include_path)
        resolved.extend(resolve_includes(include_path, project_root, _visited))
    resolved.append(doc)
    return resolved


def resolve_and_merge_project(entry_file_path):
    return merge_projects(resolve_includes(entry_file_path))


def validate_project_object(project_object, schema_spec, ssl_cert='', check_schema=True, label=None):
    json_schema = init_yaml_schema_with_checks(schema_spec,ssl_cert,check_schema)
    try:
        schema_as_object = json.loads(json_schema)
    except JSONDecodeError as err:
        raise bad_as_code_exception.BadAsCodeSchemaException(
            'This is not a valid json schema [{}] :\n{}'.format(schema_spec, err))

    validator_cls = jsonschema.validators.validator_for(schema_as_object, jsonschema.validators.Draft7Validator)
    logging.debug("Using JSON-Schema validator: %s" % validator_cls.__name__)
    v = validator_cls(schema_as_object)
    try:
        v.validate(project_object)
    except jsonschema.SchemaError as err:
        raise cli_exception.CliException('This is not a valid json schema:\n%s' % str(err))
    except jsonschema.ValidationError as err:
        msgs = ""
        for error in sorted(v.iter_errors(project_object), key=str):
            path = "\\".join(list(map(lambda x: str(x), error.path)))
            msgs += "\n" + (error.message if hasattr(error, 'message') else str(error)) + "\n\tat: " + path + "\n\tgot: \n" + (yaml.dump(error.instance) if hasattr(error, 'instance') else '') + "\n"
        msgs = ("in %s" % label if label else "") + msgs
        raise cli_exception.CliException(YAML_NOT_CONFIRM_MESSAGE + '\n' + msgs)


def validate_yaml(yaml_file_path, schema_spec, ssl_cert='', check_schema=True):
    # Resolve and merge "includes:" into one complete in-memory project before
    # validating, instead of validating this file in isolation.
    merged_project = resolve_and_merge_project(yaml_file_path)
    validate_project_object(merged_project, schema_spec, ssl_cert, check_schema, label="file %s" % yaml_file_path)


def validate_yaml_dir(path, schema_spec, ssl_cert='',continue_on_error=True):
    ignore_file = os.path.join(path, '.nlignore')
    nl_ignore_matcher =  gitignorefile.parse(ignore_file) if os.path.exists(ignore_file) else None
    extensions = ['yml','yaml','json']

    # Merge every yaml/yml/json project file found under the directory into a
    # single in-memory project, then validate that merged project once -
    # instead of validating each file (including included fragments that are
    # never meant to be a complete project on their own) in isolation.
    projects = []
    any_errs = False
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if not any(file_path.endswith("." + ext) for ext in extensions) or is_not_to_be_included(file_path, nl_ignore_matcher):
                continue
            logging.debug("file_path: {}".format(file_path))
            try:
                projects.append(parse_yaml_file(file_path))
            except Exception as err:
                any_errs = True
                if continue_on_error:
                    logging.error(str(err) + "\n")
                else:
                    raise err

    if any_errs:
        raise ValueError('One or more errors in files underneath this directory.')

    merged_project = merge_projects(projects)
    validate_project_object(merged_project, schema_spec, ssl_cert, check_schema=True, label="directory %s" % path)


def init_yaml_schema_with_checks(schema_spec, ssl_cert='', check_schema=True):
    json_schema = get_yaml_schema(False)
    if json_schema is not None:
        cached_etag = get_yaml_schema_etag()
        if cached_etag:
            logging.info('Loaded schema and ETag from disk cache.')
        else:
            logging.info('Loaded schema from disk cache (no ETag).')
        logging.debug("Cached schema %s chars, etag=%s" % (len(json_schema), cached_etag or "none"))
    else:
        logging.warning('No prior cached schema on disk.')

    if not check_schema:
        return json_schema

    schema_spec_remote = __default_schema_url
    if schema_spec is None: schema_spec = schema_spec_remote
    logging.debug("Checking schema source for changes %s" %schema_spec)

    try:
        if is_network_spec(schema_spec):
            cached_etag = get_yaml_schema_etag() if json_schema is not None else None
            json_schema_spec, response_etag, not_modified = get_network_schema_by_spec(schema_spec, ssl_cert, cached_etag)
            if not_modified:
                logging.info('Remote schema unchanged since last download (ETag match) - using cached schema.')
            elif json_schema_spec is not None:
                logging.debug("Retrieved remote schema %s chars, etag=%s" % (len(json_schema_spec), response_etag or "none"))
                if response_etag:
                    logging.info('Cached schema and ETag updated from remote source.')
                else:
                    logging.info('Cached schema updated from remote source (no ETag).')
                json_schema = json_schema_spec
                update_schema(json_schema_spec, response_etag)
            else:
                json_schema = None
        else:
            json_schema_spec = get_json_schema_by_spec(schema_spec, ssl_cert)
            if json_schema_spec is not None:
                logging.debug("Retrieved remote schema %s" %len(json_schema_spec))

            logging.info('Comparing cached schema to remote schema')
            hash_disk = "" if json_schema is None else hashlib.sha256(json_schema.encode()).hexdigest()
            hash_spec = "" if json_schema_spec is None else hashlib.sha256(json_schema_spec.encode()).hexdigest()
            if hash_disk != hash_spec:
                logging.info('Cached schema differs from source!')
                json_schema = json_schema_spec
                update_schema(json_schema_spec)
            else:
                logging.info('No differences between cached and remote schema.')
    except Exception as err:
        logging.warning('Could not update schema cache {}\n{}'.format(schema_spec,err))

    if json_schema is None:
        raise bad_as_code_exception.BadAsCodeSchemaException('Could not obtain schema definition therefore could not validate this schema.')

    return json_schema


def is_network_spec(schema_spec):
    return type(schema_spec).__name__ != 'LocalPath' and '://' in str(schema_spec)


def get_network_schema_by_spec(schema_spec, ssl_cert, cached_etag=None):
    headers = {'If-None-Match': cached_etag} if cached_etag else {}
    if cached_etag:
        logging.info('Checking for schema updates (ETag) from network source %s' % schema_spec)
    else:
        logging.info('Downloading schema from network source %s' % schema_spec)
    try:
        response = requests.get(schema_spec, headers=headers, verify=tools.ssl_cert_to_verify(ssl_cert))
    except Exception as err:
        logging.warning('Could not obtain source schema {}\n{}'.format(schema_spec, err))
        return None, cached_etag, False

    if response.status_code == 304:
        return None, cached_etag, True

    etag = response.headers.get('ETag')
    return response.text, etag if isinstance(etag, str) else None, False


def get_json_schema_by_spec(schema_spec, ssl_cert):
    json_schema_spec = None

    if type(schema_spec).__name__ == 'LocalPath':
        schema_spec = schema_spec.strpath

    if '://' in schema_spec:
        json_schema_spec, _etag, _not_modified = get_network_schema_by_spec(schema_spec, ssl_cert)
    else:
        # if user passed in a local file as the --schema-url (for local version testing purposes too)
        schema_spec = os.path.abspath(schema_spec)
        if os.path.exists(schema_spec):
            with open(schema_spec, "r") as stream:
                logging.info('Reading remote schema from storage source %s' % schema_spec)
                json_schema_spec = stream.read()
        else:
            raise bad_as_code_exception.BadAsCodeSchemaException('Could not load schema from provided file spec: %s' % schema_spec)

    return json_schema_spec
