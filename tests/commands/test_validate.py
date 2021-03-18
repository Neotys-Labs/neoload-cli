import re
import time
from unittest import mock

import pytest
from click.testing import CliRunner
from commands.validate import cli as validate
from neoload_cli_lib.user_data import __yaml_schema_file as yaml_schema_file
from neoload_cli_lib import user_data
import neoload_cli_lib.schema_validation as schema_validation
import os
import shutil


@pytest.mark.validation
class TestValidate:
    @classmethod
    def setUpClass(cls):
        shutil.rmtree(user_data.__config_dir)

    def preserve_schema(self):
        # archive existing and put it back afterwards
        local_schema_filepath = yaml_schema_file
        renamed_filepath = None
        if os.path.exists(local_schema_filepath):
            renamed_filepath = local_schema_filepath.replace(".json",".json.old")
            os.rename(local_schema_filepath,renamed_filepath)

        return (local_schema_filepath,renamed_filepath)

    def restore_schema(self,local_schema_filepath,renamed_filepath):
        # put back if there was something there at first
        if renamed_filepath is not None:
            if os.path.exists(local_schema_filepath):
                os.remove(local_schema_filepath)
            os.rename(renamed_filepath,local_schema_filepath)


    def try_success(self,file_path):
        runner = CliRunner()
        result = runner.invoke(validate, [str(file_path), '--refresh'])
        assert 'Yaml file is valid' in str(result.output)
        assert result.exit_code == 0
        return result


    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    def test_success(self, datafiles):
        return self.try_success(datafiles.listdir()[0])

    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    def test_no_refresh(self, datafiles):
        file_path = datafiles.listdir()[0]
        runner = CliRunner()
        result = runner.invoke(validate, [str(file_path)])
        assert 'Yaml file is valid' in str(result.output)
        assert result.exit_code == 0

    @pytest.mark.datafiles('tests/neoload_projects/invalid_to_schema.yaml')
    def test_error(self, datafiles):
        file_path = datafiles.listdir()[0]
        runner = CliRunner()
        result = runner.invoke(validate, [str(file_path), '--refresh'])
        assert schema_validation.YAML_NOT_CONFIRM_MESSAGE in str(result.output)
        assert result.exit_code == 1

    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    @mock.patch('requests.get', mock.Mock(return_value=mock.Mock(text="<!DOCTYPE html><html>invalid resource</html>")))
    def test_bad_schema(self, datafiles):
        file_path = datafiles.listdir()[0]
        runner = CliRunner()
        result = runner.invoke(validate, [str(file_path), '--schema-url', 'https://www.neotys.com/', '--refresh'])
        assert 'Error: This is not a valid json schema' in str(result.output)
        assert 'Expecting value: line 1 column 1' in str(result.output)
        assert result.exit_code == 1

    def test_no_argument(self):
        runner = CliRunner()
        result = runner.invoke(validate)
        assert re.compile(".*Error: Missing argument [\"']FILE[\"'].*", re.DOTALL).match(result.output) is not None
        assert result.exit_code == 2

    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    @mock.patch('requests.get', mock.Mock(side_effect=Exception("Failed to establish a new connection")))
    def test_bad_schema_url(self, datafiles):
        file_path = datafiles.listdir()[0]
        runner = CliRunner()
        result = runner.invoke(validate, [str(file_path), '--schema-url', 'http://invalid.fr', '--refresh'])
        assert 'Could not obtain schema definition' in str(result.output)
        assert result.exit_code == 1

    @pytest.mark.slow
    @mock.patch('requests.get', mock.Mock(return_value=mock.Mock(text="<i>ooi>zjfi<ezjfzioejfiozej")))
    def test_dir_with_bad_schema(self):
        result = self.try_dir_with_schema("https://www.never-use-external-resources-during-a-test-unit.com")
        assert 'not a valid json schema' in str(result.output)
        assert result.exit_code == 1

    def try_dir_with_schema(self,url):
        path = 'tests/neoload_projects/'
        runner = CliRunner()
        return runner.invoke(validate, [str(path), '--schema-url', url, '--refresh'])

    @pytest.mark.slow
    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    def test_single_with_no_prior_schema(self, datafiles):
        (l, r) = self.preserve_schema()

        # now run the actual function test and capture if failed
        err_msg = None
        try:
            self.try_success(datafiles.listdir()[0])
        except Exception as err:
            err_msg = "err: {}".format(err)

        self.restore_schema(l,r)

        # finally, if a failure occured, report it in the main thread
        assert err_msg == None, err_msg

    @pytest.mark.slow
    @pytest.mark.datafiles(
        'tests/neoload_projects/example_1/default.yaml',
        'resources/as-code.latest.schema.json'
    )
    def test_single_with_prior_schema(self, datafiles):
        datafiles_ascode = list(filter(lambda f: '.yaml' in f.strpath, datafiles.listdir()))[0]
        datafiles_schema = list(filter(lambda f: '.json' in f.strpath, datafiles.listdir()))[0]

        (l, r) = self.preserve_schema()

        # now run the actual function test and capture if failed
        err_msg = None
        try:
            result = self.try_dir_with_schema(datafiles_schema) # start with a known schema

            orig_mtime = os.path.getmtime(l)
            result = self.try_success(datafiles_ascode)
            now_mtime = os.path.getmtime(l)

            assert orig_mtime != now_mtime, 'The --refresh command did ' + \
                'not actually update the file on disk! ' + \
                'orig_mtime: {}, now_mtime: {}\nexit_code: {}\noutput: {}' \
                    .format(orig_mtime,now_mtime,result.exit_code,result.output)
        except Exception as err:
            err_msg = "err: {}".format(err)

        self.restore_schema(l,r)

        # finally, if a failure occured, report it in the main thread
        assert err_msg == None, err_msg

    @pytest.mark.slow
    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    def test_dir_with_no_prior_schema(self):
        (l, r) = self.preserve_schema()

        # now run the actual function test and capture if failed
        err_msg = None
        try:
            self.test_dir_with_bad_schema()
        except Exception as err:
            err_msg = "err: {}".format(err)

        self.restore_schema(l, r)

        # finally, if a failure occured, report it in the main thread
        assert err_msg is None, err_msg

    @pytest.mark.slow
    @pytest.mark.datafiles('resources/as-code.latest.schema.json')
    def test_dir_with_schema_url_and_refresh(self, datafiles):
        (l,r) = self.preserve_schema()

        orig_content = 'invalid schema should fail if used'
        with open(l, "w") as stream:
            stream.write(orig_content)

        # now run the actual function test and capture if failed
        err_msg = None
        try:
            file_path = datafiles.listdir()[0]
            orig_mtime = os.path.getmtime(l)
            time.sleep(1)
            result = self.try_dir_with_schema(file_path) # should modify the schema file
            # result of above matters less than its side-effects mtime change
            now_mtime = os.path.getmtime(l)
            assert orig_mtime != now_mtime, 'The --refresh command did ' + \
                'not actually update the file on disk! ' + \
                'orig_mtime: {}, now_mtime: {}\norig_content: {}\nexit_code: {}\noutput: {}' \
                    .format(orig_mtime,now_mtime,orig_content,result.exit_code,result.output)
        except Exception as err:
            err_msg = "err: {}".format(err)

        self.restore_schema(l,r)

        # finally, if a failure occured, report it in the main thread
        assert err_msg is None, err_msg
