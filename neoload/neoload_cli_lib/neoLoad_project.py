import os
import tempfile
import zipfile

import logging

from neoload_cli_lib import rest_crud, tools, cli_exception
import shutil


not_to_be_included = ['recorded-requests/', 'recorded-responses/', 'recorded-screenshots/', '.git/', '.svn/',
                      'results/', '.config/', '.neoload_cli.yaml',
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


def zip_dir(path, save):
    if save is not None:
        save = os.path.abspath(save)
        if not save.endswith(".zip"):
            raise cli_exception.CliException('If you specify where to save the zip file, it must end with .zip')
        file_stream = open(save, "w+b")
    else:
        file_stream = tempfile.NamedTemporaryFile('w+b')

    ignore_file = os.path.join(path, '.nlignore')
    nl_ignore_matcher = gitignorefile.parse(ignore_file) if os.path.exists(ignore_file) else None

    compress_project(nl_ignore_matcher, path, file_stream)

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


def find_first_nlp_file(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.nlp'):
                return os.path.join(root, file)
    return None


def zip_tes(directory, save=None):
    zip_filename = save if save else directory.rstrip(os.sep) + '.zip'
    nlp_file_path = find_first_nlp_file(directory)

    if not nlp_file_path:
        return None

    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(nlp_file_path, os.path.basename(nlp_file_path))

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if file_path == nlp_file_path:
                    continue
                zipf.write(file_path, os.path.relpath(file_path, directory))

    return zip_filename


def upload_project(path, endpoint, save=None):
    if str(path).endswith(('.zip', '.yaml', '.yml')):
        file = open(path, "br")
        filename = os.path.basename(path)
    else:
        zip_filename = zip_tes(path, save)
        if zip_filename is None:
            return
        file = open(zip_filename, "br")
        filename = os.path.basename(zip_filename)

    response = rest_crud.post_binary_files_storage(endpoint, file, filename)
    display_project(response)
    file.close()


def display_project(res):
    if 299 > res.status_code > 199:
        tools.print_json(res.json())
    else:
        print(res.text)
        raise cli_exception.CliException("Error during get meta data code: " + res.status_code)
