import os
import zipfile

from commands.project import has_password_in_zip_project, has_password_in_folder_project, upload

nlp_content_with_password = """project.name=test
project.version=8.10
project.password.hash=12vsXUgFbgL2g7u5aMuRsyhimKuEIk+jMXVD5pbkfo0=$0
"""
nlp_content = """project.name=test
project.version=8.10
"""


def create_neoload_project_zip(tmp_path, with_password):
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.writestr('test.nlp', nlp_content_with_password if with_password else nlp_content)
    return zip_path


def create_neoload_project_folder(tmp_path, with_password):
    folder_path = tmp_path / "test_project"
    if not folder_path.exists():
        os.mkdir(folder_path)
    with open(folder_path / "test.nlp", "w") as f:
        f.write(nlp_content_with_password if with_password else nlp_content)
    return folder_path


def test_has_password_in_zip_project(tmp_path):
    zip_with_password = create_neoload_project_zip(tmp_path, True)
    assert has_password_in_zip_project(zip_with_password) == True
    zip_project = create_neoload_project_zip(tmp_path, False)
    assert has_password_in_zip_project(zip_project) == False


def test_has_password_in_folder_project(tmp_path):
    folder_with_password = create_neoload_project_folder(tmp_path, True)
    assert has_password_in_folder_project(folder_with_password) == True
    folder_project = create_neoload_project_folder(tmp_path, False)
    assert has_password_in_folder_project(folder_project) == False


def test_upload_with_password(mocker, tmp_path):
    zip_with_password = create_neoload_project_zip(tmp_path, True)
    mock_upload_project = mocker.patch('commands.project.neoLoad_project.upload_project', return_value=9)
    upload(zip_with_password, "test_id", "pathToSave/file.zip")
    mock_upload_project.assert_called_once_with(zip_with_password, 'v2/tests/test_id/project', 'pathToSave/file.zip')
