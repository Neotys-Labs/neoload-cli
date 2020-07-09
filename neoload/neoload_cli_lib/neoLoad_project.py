import os
import tempfile
import zipfile

from neoload_cli_lib import rest_crud, tools, cli_exception

black_list = ['recorded-requests/', 'recorded-responses/', 'recorded-screenshots/', '.git/', '.svn/', 'results/',
              'comparative-summary/', 'reports/']


def is_black_listed(path: str):
    for refused in black_list:
        if refused in path:
            return True
    return False


def zip_dir(path):
    temp_zip = tempfile.TemporaryFile('w+b')
    ziph = zipfile.ZipFile(temp_zip, 'x', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if not is_black_listed(file_path):
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
