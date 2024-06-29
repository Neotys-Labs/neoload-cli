import pytest
import zipfile
from pathlib import Path
from commands.project import extract_nlp_from_zip, find_password_in_nlp, upload


@pytest.fixture
def create_test_zip(tmp_path):
    zip_path = tmp_path / "test.zip"
    nlp_content = """project.name=test
project.version=8.10
project.password.hash=12vsXUgFbgL2g7u5aMuRsyhimKuEIk+jMXVD5pbkfo0=$0
"""
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.writestr('test.nlp', nlp_content)
    return zip_path


def test_extract_nlp_from_zip(create_test_zip):
    zip_path = create_test_zip
    nlp_file = extract_nlp_from_zip(zip_path)
    assert nlp_file is not None
    assert nlp_file.name == 'test.nlp'


def test_find_password_in_nlp(create_test_zip):
    zip_path = create_test_zip
    nlp_file = extract_nlp_from_zip(zip_path)
    password = find_password_in_nlp(nlp_file)
    assert password == "12vsXUgFbgL2g7u5aMuRsyhimKuEIk+jMXVD5pbkfo0=$0"


def test_upload_with_password(mocker, tmp_path):
    zip_path = tmp_path / "test.zip"
    nlp_content = """project.name=test
project.version=8.10
project.password.hash=12vsXUgFbgL2g7u5aMuRjsyhimKuEIk+jMXVD5pbkfo0=$0
"""
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.writestr('test.nlp', nlp_content)

    mock_upload_project = mocker.patch('commands.project.neoLoad_project.upload_project', return_value=9)
    upload(zip_path, "test_id", "pathToSave/file.zip")
    mock_upload_project.assert_called_once_with(zip_path, 'v2/tests/test_id/project', 'pathToSave/file.zip')


def test_upload_password(mocker, tmp_path):
    zip_path = tmp_path / "test.zip"
    nlp_content = """project.name=test
project.version=8.10
project.password.hash=12vsXUgFbgL2g7u5aMuRsyhimKuEIk+jMXVD5pbkfo0=$0
"""
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.writestr('test.nlp', nlp_content)

    mock_upload_project = mocker.patch('commands.project.neoLoad_project.upload_project', return_value=9)
    upload(zip_path, "test_id", "pathToSave/file.zip")
    mock_upload_project.assert_called_once_with(zip_path, 'v2/tests/test_id/project', 'pathToSave/file.zip')
