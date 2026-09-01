from unittest import mock

import pytest
from click.testing import CliRunner

from commands.checkvu import cli as checkvu
from neoload_cli_lib import checkvu_runner
import neoload_cli_lib.schema_validation as schema_validation


class FakeJarResponse:
    def __init__(self, content=b"PK\x03\x04jar", filename="checkvu_2026_3_0_linux.jar",
                 url=None, status_code=200):
        self.content = content
        self.status_code = status_code
        self.url = url or ("https://cdn.example/" + filename)
        self.headers = {
            "Content-Disposition": 'attachment; filename="{0}"'.format(filename),
            "content-length": str(len(content)),
        }
        self.iter_content_calls = 0

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("HTTP {0}".format(self.status_code))

    def iter_content(self, chunk_size=64):
        self.iter_content_calls += 1
        yield self.content

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


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

    @pytest.mark.parametrize("system,machine,expected", [
        ("Linux", "x86_64", "linux"),
        ("Linux", "amd64", "linux"),
        ("Linux", "aarch64", "linux-arm64"),
        ("Linux", "arm64", "linux-arm64"),
        ("Darwin", "x86_64", "mac"),
        ("Darwin", "arm64", "mac_arm64"),
        ("Windows", "AMD64", "win32_x64"),
        ("Windows", "x86_64", "win32_x64"),
    ])
    def test_detect_os(self, system, machine, expected):
        assert checkvu_runner.detect_os(system, machine) == expected

    def test_detect_os_windows_arm_unsupported(self):
        with pytest.raises(checkvu_runner.cli_exception.CliException) as err:
            checkvu_runner.detect_os("Windows", "ARM64")
        assert "Windows ARM" in str(err.value)

    def test_detect_os_unknown_fails(self):
        with pytest.raises(checkvu_runner.cli_exception.CliException) as err:
            checkvu_runner.detect_os("SunOS", "sparc")
        assert "Unsupported platform" in str(err.value)

    def test_build_redirect_url(self):
        url = checkvu_runner.build_redirect_url("linux")
        assert url == (
            "https://www.neotys.com/redirect/redirect.php"
            "?product=checkvu&target=direct-download&os=linux&version=latest&format=jar"
        )

    def test_build_redirect_url_all_platforms(self):
        for os_name in checkvu_runner.SUPPORTED_OS:
            url = checkvu_runner.build_redirect_url(os_name)
            assert "product=checkvu" in url
            assert "target=direct-download" in url
            assert "os={0}".format(os_name) in url
            assert "version=latest" in url
            assert "format=jar" in url
            assert "neoload-version" not in url
            assert "checkvu-version" not in url

    def test_version_from_filename(self):
        assert checkvu_runner.version_from_filename("checkvu_2026_3_0_linux.jar") == "2026.3.0"
        assert checkvu_runner.version_from_filename("checkvu_2026_3_0_win32_x64.jar") == "2026.3.0"
        assert checkvu_runner.version_from_filename("neoload-checkvu-cli.jar") is None

    def test_filename_from_response_content_disposition(self):
        response = mock.Mock(
            headers={"Content-Disposition": 'attachment; filename="checkvu_2026_3_0_mac_arm64.jar"'},
            url="https://www.neotys.com/redirect/redirect.php?product=checkvu",
        )
        assert checkvu_runner.filename_from_response(response) == "checkvu_2026_3_0_mac_arm64.jar"

    def test_filename_from_response_final_url(self):
        response = mock.Mock(
            headers={},
            url="https://cdn.example/documents/download/checkvu/v2026.3/checkvu_2026_3_0_linux.jar",
        )
        assert checkvu_runner.filename_from_response(response) == "checkvu_2026_3_0_linux.jar"

    def test_resolve_jar_uses_explicit_local_path(self, tmp_path):
        jar = tmp_path / "checkvu.jar"
        jar.write_text("x")
        with mock.patch.object(checkvu_runner, "download_jar") as dl:
            assert checkvu_runner.resolve_jar(engine_jar=str(jar)) == str(jar)
        dl.assert_not_called()

    def test_resolve_jar_explicit_local_path_missing_fails(self, tmp_path):
        missing = tmp_path / "missing.jar"
        with pytest.raises(checkvu_runner.cli_exception.CliException) as err:
            checkvu_runner.resolve_jar(engine_jar=str(missing))
        assert "not found" in str(err.value)

    def test_resolve_jar_downloads_explicit_url(self, tmp_path):
        with mock.patch.object(checkvu_runner, "download_jar", return_value="downloaded.jar") as dl:
            result = checkvu_runner.resolve_jar(engine_jar="https://example.com/checkvu.jar")
        assert result == "downloaded.jar"
        dl.assert_called_once_with("https://example.com/checkvu.jar", "")

    def test_resolve_jar_uses_redirect_for_latest_when_nothing_cached(self, tmp_path):
        redirect = checkvu_runner.build_redirect_url("linux")
        with mock.patch.object(checkvu_runner, "detect_os", return_value="linux"), \
                mock.patch.object(checkvu_runner, "get_cached_jar_path", return_value=None), \
                mock.patch.object(checkvu_runner, "download_jar", return_value="downloaded.jar") as dl:
            result = checkvu_runner.resolve_jar()
        assert result == "downloaded.jar"
        dl.assert_called_once_with(redirect, "")

    def test_resolve_jar_reuses_cache_without_a_network_call(self, tmp_path):
        cached = tmp_path / "checkvu_2026_3_0_linux.jar"
        cached.write_bytes(b"PK\x03\x04cached")
        with mock.patch.object(checkvu_runner, "get_cached_jar_path", return_value=str(cached)), \
                mock.patch.object(checkvu_runner, "download_jar") as dl:
            result = checkvu_runner.resolve_jar()
        assert result == str(cached)
        dl.assert_not_called()

    def test_resolve_jar_download_failure_mentions_the_jar_option(self, tmp_path):
        with mock.patch.object(checkvu_runner, "get_cached_jar_path", return_value=None), \
                mock.patch.object(checkvu_runner, "download_jar",
                                  side_effect=checkvu_runner.cli_exception.CliException(
                                      "Failed to download the CheckVU JAR from 'https://...': 403")):
            with pytest.raises(checkvu_runner.cli_exception.CliException) as err:
                checkvu_runner.resolve_jar()
        assert "--jar" in str(err.value)

    def test_cache_keeps_only_latest_jar(self, tmp_path):
        old = tmp_path / "checkvu_2026_2_0_linux.jar"
        old.write_bytes(b"PK\x03\x04old")
        response = FakeJarResponse(filename="checkvu_2026_3_0_linux.jar", content=b"PK\x03\x04new")
        with mock.patch.object(checkvu_runner, "get_cache_dir", return_value=str(tmp_path)), \
                mock.patch.object(checkvu_runner.requests, "get", return_value=response):
            result = checkvu_runner.download_jar("https://www.neotys.com/redirect/redirect.php?os=linux")
        assert result == str(tmp_path / "checkvu_2026_3_0_linux.jar")
        assert not old.exists()
        assert (tmp_path / "checkvu_2026_3_0_linux.jar").read_bytes() == b"PK\x03\x04new"
        assert [p.name for p in tmp_path.glob("*.jar")] == ["checkvu_2026_3_0_linux.jar"]

    def test_cache_reuses_same_filename_without_redownload(self, tmp_path):
        cached = tmp_path / "checkvu_2026_3_0_linux.jar"
        cached.write_bytes(b"PK\x03\x04cached")
        response = FakeJarResponse(filename="checkvu_2026_3_0_linux.jar", content=b"PK\x03\x04new")
        with mock.patch.object(checkvu_runner, "get_cache_dir", return_value=str(tmp_path)), \
                mock.patch.object(checkvu_runner.requests, "get", return_value=response):
            result = checkvu_runner.download_jar("https://www.neotys.com/redirect/redirect.php?os=linux")
        assert result == str(cached)
        assert cached.read_bytes() == b"PK\x03\x04cached"
        assert response.iter_content_calls == 0

    def test_download_rejects_non_jar_payload(self, tmp_path):
        response = FakeJarResponse(filename="checkvu_2026_3_0_linux.jar", content=b"<html>nope</html>")
        with mock.patch.object(checkvu_runner, "get_cache_dir", return_value=str(tmp_path)), \
                mock.patch.object(checkvu_runner.requests, "get", return_value=response):
            with pytest.raises(checkvu_runner.cli_exception.CliException) as err:
                checkvu_runner.download_jar("https://www.neotys.com/redirect/redirect.php?os=linux")
        assert "did not return a JAR" in str(err.value)
        assert list(tmp_path.glob("*.jar")) == []


@pytest.mark.validation
class TestCheckvuCommand:
    def _yaml_file(self, tmp_path):
        p = tmp_path / "project.yaml"
        p.write_text("name: test")
        return str(p)

    def test_download_failure_is_reported(self, tmp_path):
        runner = CliRunner()
        project = self._yaml_file(tmp_path)
        with mock.patch.object(schema_validation, 'validate_path', return_value='Yaml file is valid.'), \
                mock.patch.object(checkvu_runner, 'resolve_java', return_value="java"), \
                mock.patch.object(checkvu_runner, 'check_java_version', return_value=21), \
                mock.patch.object(checkvu_runner, 'get_cached_jar_path', return_value=None), \
                mock.patch.object(checkvu_runner, 'download_jar',
                                  side_effect=checkvu_runner.cli_exception.CliException(
                                      "Failed to download the CheckVU JAR")):
            result = runner.invoke(checkvu, [project])
        assert result.exit_code == 1
        assert "Failed to download the CheckVU JAR" in result.output
        assert "--jar" in result.output

    def test_old_java_fails_before_run(self, tmp_path):
        runner = CliRunner()
        project = self._yaml_file(tmp_path)
        completed = mock.Mock(stdout='openjdk version "17.0.10" 2024-01-16 LTS')
        with mock.patch.object(schema_validation, 'validate_path', return_value='Yaml file is valid.'), \
                mock.patch.object(checkvu_runner, 'resolve_java', return_value="java"), \
                mock.patch('subprocess.run', return_value=completed) as run_mock, \
                mock.patch.object(checkvu_runner, 'download_jar') as dl:
            result = runner.invoke(checkvu, [project, "--jar", "x.jar"])
        assert result.exit_code == 1
        assert "requires Java 21" in result.output
        assert run_mock.call_count == 1
        dl.assert_not_called()

    def test_jar_option_skips_download(self, tmp_path):
        runner = CliRunner()
        project = self._yaml_file(tmp_path)
        jar = tmp_path / "patched.jar"
        jar.write_text("x")
        recorded = {}

        def fake_run(command, *args, **kwargs):
            recorded['command'] = command
            return mock.Mock(returncode=0)

        with mock.patch.object(schema_validation, 'validate_path', return_value='Yaml file is valid.'), \
                mock.patch.object(checkvu_runner, 'resolve_java', return_value="java"), \
                mock.patch.object(checkvu_runner, 'check_java_version', return_value=21), \
                mock.patch.object(checkvu_runner, 'download_jar') as dl, \
                mock.patch('subprocess.run', side_effect=fake_run):
            result = runner.invoke(checkvu, [project, "--jar", str(jar)])
        assert result.exit_code == 0
        dl.assert_not_called()
        assert recorded['command'] == ["java", "-jar", str(jar), project]

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