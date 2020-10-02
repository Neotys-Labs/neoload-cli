import os
import tempfile
import zipfile

import logging
from gitignore_parser import parse_gitignore

from neoload_cli_lib import rest_crud, tools, cli_exception

black_list = ['recorded-requests/', 'recorded-responses/', 'recorded-screenshots/', '.git/', '.svn/', 'results/',
              'comparative-summary/', 'reports/']


def is_black_listed(path: str, nlignore_matcher):
    for refused in black_list:
        if refused in path:
            logging.debug("blacklisted: '" + path + "'")
            return True
    if nlignore_matcher is not None and nlignore_matcher(path):
        logging.debug(".nlignore'd: '" + path + "'")
        return True
    return False


def zip_dir(path):
    # find and load .nlignore
    ignorefile = os.path.join(path, '.nlignore')
    nlignore_matcher = parse_gitignore(ignorefile) if os.path.exists(ignorefile) else None

    temp_zip = tempfile.TemporaryFile('w+b')
    ziph = zipfile.ZipFile(temp_zip, 'x', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if not is_black_listed(file_path, nlignore_matcher):
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
    display_project(rest_crud.post_binary_files_storage(endpoint, file, filename))


def display_project(res):
    if 299 > res.status_code > 199:
        tools.print_json(res.json())
    else:
        print(res.text)
        raise cli_exception.CliException("Error during get meta data code: " + res.status_code)
