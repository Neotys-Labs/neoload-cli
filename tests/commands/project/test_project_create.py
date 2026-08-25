import os

from click.testing import CliRunner
from commands.project import cli as project


class TestProjectCreate:
    def test_creates_project_with_demo_yaml(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(project, ['create', 'my-demo'])
            assert result.exit_code == 0, result.output
            assert "Project 'my-demo' created successfully." in result.output
            assert os.path.join('my-demo', 'default.yaml') in result.output
            assert f"neoload checkvu {os.path.join('my-demo', 'default.yaml')}" in result.output

            yaml_path = os.path.join('my-demo', 'default.yaml')
            assert os.path.isfile(yaml_path)
            with open(yaml_path, encoding='utf-8') as f:
                content = f.read()
            assert 'name: DemoWebShop' in content
            assert 'demowebshop.tricentis.com' in content
            assert 'from this project directory' in content

    def test_trims_project_name(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(project, ['create', '  my-demo  '])
            assert result.exit_code == 0, result.output
            assert "Project 'my-demo' created successfully." in result.output
            assert os.path.isfile(os.path.join('my-demo', 'default.yaml'))

    def test_fails_when_folder_already_exists(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            os.mkdir('existing')
            result = runner.invoke(project, ['create', 'existing'])
            assert result.exit_code == 1
            assert "path already exists" in result.output

    def test_rejects_path_as_project_name(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(project, ['create', os.path.join('nested', 'project')])
            assert result.exit_code == 1
            assert "not a path" in result.output

    def test_missing_project_name(self):
        runner = CliRunner()
        result = runner.invoke(project, ['create'])
        assert result.exit_code == 1
        assert "Missing project name" in result.output
