import os
import tempfile
import zipfile

import logging
from gitignore_parser import parse_gitignore

from neoload_cli_lib import rest_crud, tools, cli_exception

not_to_be_included = ['recorded-requests/', 'recorded-responses/', 'recorded-screenshots/', '.git/', '.svn/', 'results/',
              'comparative-summary/', 'reports/', '/recorded-artifacts/']


def is_not_to_be_included(path: str, nlignore_matcher):
    for refused in not_to_be_included:
        if refused in path:
            logging.debug("not_included: '" + path + "'")
            return True
    if nlignore_matcher is not None and nlignore_matcher(path):
        logging.debug(".nlignore'd: '" + path + "'")
        return True
    return False


def zip_dir(path):
    # find and load .nlignore
    ignorefile = os.path.join(path, '.nlignore')
    nlignore_matcher = parse_gitignore(ignorefile) if os.path.exists(ignorefile) else None

    temp_zip = tempfile.NamedTemporaryFile('w+b')
    ziph = zipfile.ZipFile(temp_zip, 'x', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if not is_not_to_be_included(file_path, nlignore_matcher):
                ziph.write(file_path, file_path.replace(str(path), ''))

    ziph.close()
    temp_zip.seek(0)
    return temp_zip


def upload_project(path, endpoint):
    filename = os.path.basename(path)
    if str(path).endswith(('.zip', '.yaml', '.yml')):
        file = open(path, "b+r")
    else:
        filename += '.zip'
        file = zip_dir(path)

    totalsize = os.stat(file.name).st_size

    if totalsize < (100 * 1000): # if over 100KB, use with progress
        display_project(rest_crud.post_binary_files_storage(endpoint, file, filename))
    else:
        display_project(rest_crud.post_binary_files_storage_with_progress(endpoint, file, filename))



def display_project(res):
    if 299 > res.status_code > 199:
        tools.print_json(res.json())
    else:
        print(res.text)
        raise cli_exception.CliException("Error during get meta data code: " + res.status_code)
