from unittest import mock

import pytest
from click.testing import CliRunner

from commands.checkvu import cli as checkvu
from neoload_cli_lib import checkvu_runner
import neoload_cli_lib.schema_validation as schema_validation


class TestCheckvuRunner:
    @pytest.mark.parametrize("output,expected", [
        ('openjdk version "21.0.2" 2024-01-16', 21),
        ('java version "17.0.10" 2024-01-16 LTS', 17),
        ('openjdk version "1.8.0_402"', 8),
        ('something without a version', None),
    ])
    def test_parse_java_major_version(self, output, expected):
        assert checkvu_runner.parse_java_major_version(output) == expected

    def test_check_java_version_too_old(self):
        completed = mock.Mock(stdout='openjdk version "17.0.10" 2024-01-16 LTS')
        with mock.patch('subprocess.run', return_value=completed):
            with pytest.raises(checkvu_runner.cli_exception.CliException) as err:
                checkvu_runner.check_java_version("java")
        assert "requires Java 21" in str(err.value)

    def test_check_java_version_ok(self):
        completed = mock.Mock(stdout='openjdk version "21.0.2" 2024-01-16')
        with mock.patch('subprocess.run', return_value=completed):
            assert checkvu_runner.check_java_version("java") == 21

    def test_build_command(self):
        command = checkvu_runner.build_command("java", "checkvu.jar", "p.yaml",
                                               user_path="myUser")
        assert command == ["java", "-jar", "checkvu.jar", "--user-path", "myUser", "p.yaml"]

    def test_build_command_minimal(self):
        command = checkvu_runner.build_command("java", "checkvu.jar", "p.yaml")
        assert command == ["java", "-jar", "checkvu.jar", "p.yaml"]

    def test_build_command_overlays(self):
        command = checkvu_runner.build_command(
            "java", "checkvu.jar", "p.yaml",
            controller_properties="/tmp/ctrl.properties",
            load_generator_properties="/tmp/agent.properties",
        )
        assert command == [
            "java", "-jar", "checkvu.jar",
            "--controller-properties", "/tmp/ctrl.properties",
            "--load-generator-properties", "/tmp/agent.properties",
            "p.yaml",
        ]

    def test_build_command_proxy(self):
        command = checkvu_runner.build_command(
            "java", "checkvu.jar", "p.yaml",
            app_proxy="proxy.corp:8080",
            app_proxy_username="alice",
            app_proxy_bypass="localhost,internal",
        )
        assert command == [
            "java", "-jar", "checkvu.jar",
            "--app-proxy", "proxy.corp:8080",
            "--app-proxy-username", "alice",
            "--app-proxy-bypass", "localhost,internal",
            "p.yaml",
        ]

    def test_build_command_keep_temp_work_dir(self):
        command = checkvu_runner.build_command("java", "checkvu.jar", "p.yaml", keep_temp_work_dir=True)
        assert command == ["java", "-jar", "checkvu.jar", "--keep-temp-work-dir", "p.yaml"]

    def test_build_command_work_dir(self):
        command = checkvu_runner.build_command("java", "checkvu.jar", "p.yaml", work_dir="/tmp/scratch")
        assert command == ["java", "-jar", "checkvu.jar", "--work-dir", "/tmp/scratch", "p.yaml"]

    @pytest.mark.parametrize("spec,expected", [
        ("https://example.com/checkvu.jar", True),
        ("http://example.com/checkvu.jar", True),
        ("/tmp/checkvu.jar", False),
        ("C:\\jars\\checkvu.jar", False),
        (None, False),
    ])
    def test_is_url(self, spec, expected):
        assert checkvu_runner.is_url(spec) == expected

    def test_resolve_jar_uses_explicit_local_path(self, tmp_path):
        jar = tmp_path / "checkvu.jar"
        jar.write_text("x")
        assert checkvu_runner.resolve_jar(engine_jar=str(jar)) == str(jar)

    def test_resolve_jar_explicit_local_path_missing_fails(self, tmp_path):
        missing = tmp_path / "missing.jar"
        with pytest.raises(checkvu_runner.cli_exception.CliException) as err:
            checkvu_runner.resolve_jar(engine_jar=str(missing))
        assert "not found" in str(err.value)

    def test_resolve_jar_downloads_explicit_url(self, tmp_path):
        cached = tmp_path / "cached.jar"
        with mock.patch.object(checkvu_runner, 'get_cached_jar_path', return_value=str(cached)), \
                mock.patch.object(checkvu_runner, 'download_jar', return_value="downloaded.jar") as dl:
            result = checkvu_runner.resolve_jar(engine_jar="https://example.com/checkvu.jar")
        assert result == "downloaded.jar"
        dl.assert_called_once()

    def test_resolve_jar_uses_cache(self, tmp_path):
        cached = tmp_path / "cached.jar"
        cached.write_text("x")
        with mock.patch.object(checkvu_runner, 'get_cached_jar_path', return_value=str(cached)):
            assert checkvu_runner.resolve_jar() == str(cached)

    def test_resolve_jar_downloads_when_no_cache(self, tmp_path):
        cached = tmp_path / "missing.jar"
        with mock.patch.object(checkvu_runner, 'get_cached_jar_path', return_value=str(cached)), \
                mock.patch.object(checkvu_runner, 'download_jar', return_value="downloaded.jar") as dl, \
                mock.patch.object(checkvu_runner, 'DEFAULT_JAR_URL', "http://example/default.jar"):
            result = checkvu_runner.resolve_jar()
        assert result == "downloaded.jar"
        dl.assert_called_once()


@pytest.mark.validation
class TestCheckvuCommand:
    def _yaml_file(self, tmp_path):
        p = tmp_path / "project.yaml"
        p.write_text("name: test")
        return str(p)

    def test_jar_not_found(self, tmp_path):
        runner = CliRunner()
        project = self._yaml_file(tmp_path)
        with mock.patch.object(schema_validation, 'validate_path', return_value='Yaml file is valid.'), \
                mock.patch.object(checkvu_runner, 'resolve_java', return_value="java"), \
                mock.patch.object(checkvu_runner, 'check_java_version', return_value=21), \
                mock.patch.object(checkvu_runner, 'get_cached_jar_path', return_value="/does/not/exist.jar"), \
                mock.patch.object(checkvu_runner, 'DEFAULT_JAR_URL', ""):
            result = runner.invoke(checkvu, [project])
        assert result.exit_code == 1
        assert "No CheckVU JAR available" in result.output

    def test_old_java_fails_before_run(self, tmp_path):
        runner = CliRunner()
        project = self._yaml_file(tmp_path)
        completed = mock.Mock(stdout='openjdk version "17.0.10" 2024-01-16 LTS')
        with mock.patch.object(schema_validation, 'validate_path', return_value='Yaml file is valid.'), \
                mock.patch.object(checkvu_runner, 'resolve_java', return_value="java"), \
                mock.patch('subprocess.run', return_value=completed) as run_mock:
            result = runner.invoke(checkvu, [project, "--engine-jar", "x.jar"])
        assert result.exit_code == 1
        assert "requires Java 21" in result.output
        assert run_mock.call_count == 1

    def test_argv_assembly_and_exit_code(self, tmp_path):
        runner = CliRunner()
        project = self._yaml_file(tmp_path)
        recorded = {}

        def fake_run(command, *args, **kwargs):
            recorded['command'] = command
            return mock.Mock(returncode=0)

        with mock.patch.object(schema_validation, 'validate_path', return_value='Yaml file is valid.'), \
                mock.patch.object(checkvu_runner, 'resolve_java', return_value="java"), \
                mock.patch.object(checkvu_runner, 'check_java_version', return_value=21), \
                mock.patch.object(checkvu_runner, 'resolve_jar', return_value="checkvu.jar"), \
                mock.patch('subprocess.run', side_effect=fake_run):
            result = runner.invoke(checkvu, [project])
        assert result.exit_code == 0
        assert recorded['command'] == ["java", "-jar", "checkvu.jar", project]

    def test_nonzero_exit_code(self, tmp_path):
        runner = CliRunner()
        project = self._yaml_file(tmp_path)
        with mock.patch.object(schema_validation, 'validate_path', return_value='Yaml file is valid.'), \
                mock.patch.object(checkvu_runner, 'resolve_java', return_value="java"), \
                mock.patch.object(checkvu_runner, 'check_java_version', return_value=21), \
                mock.patch.object(checkvu_runner, 'resolve_jar', return_value="checkvu.jar"), \
                mock.patch('subprocess.run', return_value=mock.Mock(returncode=3)):
            result = runner.invoke(checkvu, [project])
        assert result.exit_code == 3

    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    def test_validates_yaml_before_run(self, datafiles):
        runner = CliRunner()
        project = str(datafiles / 'default.yaml')
        with mock.patch.object(schema_validation, 'validate_path', return_value='Yaml file is valid.') as vp, \
                mock.patch.object(checkvu_runner, 'resolve_java', return_value="java"), \
                mock.patch.object(checkvu_runner, 'check_java_version', return_value=21), \
                mock.patch.object(checkvu_runner, 'resolve_jar', return_value="checkvu.jar"), \
                mock.patch('subprocess.run', return_value=mock.Mock(returncode=0)):
            result = runner.invoke(checkvu, [project])
        assert result.exit_code == 0
        vp.assert_called_once()

    @pytest.mark.datafiles('tests/neoload_projects/example_1/default.yaml')
    def test_as_code_schema_overrides_default_schema(self, datafiles):
        runner = CliRunner()
        project = str(datafiles / 'default.yaml')
        with mock.patch.object(schema_validation, 'validate_path', return_value='Yaml file is valid.') as vp, \
                mock.patch.object(checkvu_runner, 'resolve_java', return_value="java"), \
                mock.patch.object(checkvu_runner, 'check_java_version', return_value=21), \
                mock.patch.object(checkvu_runner, 'resolve_jar', return_value="checkvu.jar"), \
                mock.patch('subprocess.run', return_value=mock.Mock(returncode=0)):
            result = runner.invoke(checkvu, [project, "-s", "https://custom.example/schema.json"])
        assert result.exit_code == 0
        assert vp.call_args.args[1] == "https://custom.example/schema.json"