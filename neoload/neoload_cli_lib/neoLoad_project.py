import os
import tempfile
import zipfile

import logging
from gitignore_parser import parse_gitignore

from neoload_cli_lib import rest_crud, tools, cli_exception
import shutil

not_to_be_included = ['recorded-requests/', 'recorded-responses/', 'recorded-screenshots/', '.git/', '.svn/',
                      'results/','.config/',
                      'comparative-summary/', 'reports/', '/recorded-artifacts/']


def is_not_to_be_included(path: str, nl_ignore_matcher):
    for refused in not_to_be_included:
        if refused in path:
            logging.debug("not_included: '" + path + "'")
            return True
    if nl_ignore_matcher is not None and nl_ignore_matcher(path):
        logging.debug(".nlignore'd: '" + path + "'")
        return True
    return False


def zip_dir(path,save):
    # validate save parameter, if provided, is a zip
    if save is not None:
        save = os.path.abspath(save)
        if not save.endswith(".zip"):
            raise cli_exception.CliException('If you specify where to save the zip file, it must end with .zip')
        file_stream = open(save, "w+b")
    else:
        # always to work in a separate file, if save is provided, or otherwise
        file_stream = tempfile.NamedTemporaryFile('w+b')

    # find and load .nlignore
    ignore_file = os.path.join(path, '.nlignore')
    nl_ignore_matcher = parse_gitignore(ignore_file) if os.path.exists(ignore_file) else None

    compress_project(nl_ignore_matcher, path, file_stream)

    # always ensure that stream starts at beginning
    file_stream.seek(0)

    return file_stream


def compress_project(nl_ignore_matcher, path, temp_zip):
    ziph = zipfile.ZipFile(temp_zip, 'x', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if not is_not_to_be_included(file_path, nl_ignore_matcher):
                ziph.write(file_path, file_path.replace(str(path), ''))
    ziph.close()


def upload_project(path, endpoint, save=None):
    filename = os.path.basename(path)
    if str(path).endswith(('.zip', '.yaml', '.yml')):
        file = open(path, "b+r")
    else:
        filename += '.zip'
        file = zip_dir(path,save)

    display_project(rest_crud.post_binary_files_storage(endpoint, file, filename))

def display_project(res):
    if 299 > res.status_code > 199:
        tools.print_json(res.json())
    else:
        print(res.text)
        raise cli_exception.CliException("Error during get meta data code: " + res.status_code)
