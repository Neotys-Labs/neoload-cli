import os
import zipfile
import tempfile
import click

from neoload_cli_lib import rest_crud, tools

black_list = ['recorded-requests/', 'recorded-responses/', 'recorded-screenshots/', '.git/', '.svn/']


def add_or_not(path: str):
    for refused in black_list:
        if refused in path:
            return False
    return True


def zip_dir(path):
    temp_zip = tempfile.TemporaryFile('w+b')
    ziph = zipfile.ZipFile(temp_zip, 'x', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if add_or_not(file_path):
                ziph.write(file_path)
    ziph.close()
    temp_zip.seek(0)
    return temp_zip


def upload_project(path, endpoint):
    filename = os.path.basename(path) + '.zip'
    file = zip_dir(path)
    display_project(rest_crud.post_binary_files_storage(endpoint, file, filename))


def display_project(res):
    if 299 > res.status_code > 199:
        tools.print_json(res.json())
    else:
        print(res.text)
        raise click.ClickException("Error during get meta data code: " + res.status_code)
