import os
import zipfile
import tempfile
import yaml

from neoload_cli_lib import rest_crud


def zip_dir(path):
    temp_zip = tempfile.TemporaryFile('wb')
    ziph = zipfile.ZipFile(temp_zip, 'wx', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))
    ziph.close()
    return temp_zip


def upload_project(path, endpoint):
    file = zip_dir(path)
    rest_crud.post_binary(endpoint, file)
    file.delete()

