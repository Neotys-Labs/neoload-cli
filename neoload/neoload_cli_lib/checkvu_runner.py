import os
import re
import shutil
import subprocess
import sys

from neoload_cli_lib import cli_exception, paths

MIN_JAVA_VERSION = 21

# Default download URL pointing at the "latest" CheckVU JAR
# TODO: set this once we have public jar url
# use --engine-jar for now
DEFAULT_JAR_URL = ""

CACHE_DIR_NAME = "checkvu"
CACHE_JAR_NAME = "neoload-checkvu-cli.jar"

__java_version_pattern = re.compile(r'version "(\d+)(?:\.(\d+))?')


def get_cache_dir():
    return os.path.join(paths.get_config_dir(), CACHE_DIR_NAME)


def get_cached_jar_path():
    return os.path.join(get_cache_dir(), CACHE_JAR_NAME)


def resolve_java(java_option=None):
    """Return the path to a usable java executable, raising if none is found."""
    if java_option:
        return java_option
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidate = os.path.join(java_home, "bin", "java")
        resolved = shutil.which(candidate) or (candidate if os.path.isfile(candidate) else None)
        if resolved:
            return resolved
    found = shutil.which("java")
    if found:
        return found
    raise cli_exception.CliException(
        "No Java runtime found. CheckVU requires Java {0} or later.\n"
        "Install a JDK {0}+ and either add it to your PATH, set JAVA_HOME, "
        "or pass --java <path-to-java>.".format(MIN_JAVA_VERSION))


def parse_java_major_version(version_output):
    """Extract the major Java version from `java -version` output, or None."""
    match = __java_version_pattern.search(version_output)
    if match is None:
        return None
    major = int(match.group(1))
    # Legacy versions 1.x -> x
    if major == 1 and match.group(2) is not None:
        return int(match.group(2))
    return major


def check_java_version(java):
    """Runs `java -version` and enforces the minimum supported major version.
    `java -version` writes to stderr, so we merge stderr into stdout to capture it.
    """
    try:
        completed = subprocess.run(
            [java, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True)
    except OSError as err:
        raise cli_exception.CliException(
            "Unable to run '{0}': {1}\n"
            "Install a JDK {2}+ and either add it to your PATH, set JAVA_HOME, "
            "or pass --java <path-to-java>.".format(java, str(err), MIN_JAVA_VERSION))

    output = completed.stdout or ""
    major = parse_java_major_version(output)
    if major is None:
        raise cli_exception.CliException(
            "Could not determine the Java version from '{0} -version':\n{1}".format(java, output.strip()))
    if major < MIN_JAVA_VERSION:
        raise cli_exception.CliException(
            "CheckVU requires Java {0} or later, but '{1}' reports major version {2}.\n"
            "Install a JDK {0}+ and either add it to your PATH, set JAVA_HOME, "
            "or pass --java <path-to-java>.".format(MIN_JAVA_VERSION, java, major))
    return major

def is_url(spec):
    return spec is not None and '://' in spec


# TODO cache invalidation according to project version ?
def resolve_jar(engine_jar=None, ssl_cert=''):
    """Resolves the CheckVU fat JAR from --engine-jar (a local file, or a download URL).
    Resolution order:
      1. --engine-jar
      2. cached JAR if exists
      3. DEFAULT_JAR_URL -> download + cache
      4. error
    """
    cache_path = get_cached_jar_path()

    if engine_jar:
        if is_url(engine_jar):
            return download_jar(engine_jar, cache_path, ssl_cert)
        if not os.path.isfile(engine_jar):
            raise cli_exception.CliException("CheckVU JAR not found at '{0}'.".format(engine_jar))
        return engine_jar

    if os.path.isfile(cache_path):
        return cache_path

    if DEFAULT_JAR_URL:
        return download_jar(DEFAULT_JAR_URL, cache_path, ssl_cert)

    raise cli_exception.CliException(
        "No CheckVU JAR available. Provide one with --engine-jar <path-to-neoload-checkvu-cli.jar|download-url>.\n")


def download_jar(url, destination, ssl_cert=''):
    """Download the CheckVU JAR to the cache, showing a progress bar when interactive."""
    import requests
    from tqdm import tqdm
    from neoload_cli_lib import tools

    verify = tools.ssl_cert_to_verify(ssl_cert)
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    partial_destination = destination + ".part"
    print("Downloading JAR from " + url + "\n")
    try:
        with requests.get(url, stream=True, verify=verify) as response:
            response.raise_for_status()
            total_bytes = int(response.headers.get("content-length", 0))
            progress_bar = None
            if tools.is_user_interactive():
                progress_bar = tqdm(desc=CACHE_JAR_NAME, total=total_bytes, unit="B",
                                    unit_scale=True, leave=False, dynamic_ncols=True)
            with open(partial_destination, "wb") as stream:
                for chunk in response.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        stream.write(chunk)
                        if progress_bar is not None:
                            progress_bar.update(len(chunk))
            if progress_bar is not None:
                progress_bar.close()
        os.replace(partial_destination, destination)
    except Exception as err:
        if os.path.isfile(partial_destination):
            os.remove(partial_destination)
        raise cli_exception.CliException(
            "Failed to download the CheckVU JAR from '{0}':\n{1}".format(url, str(err)))
    return destination


# LOAD-39125: CheckVU CLI JVM flags. Passed on the java command line only — not JAVA_TOOL_OPTIONS
# (the Load Generator child process would inherit them).
CHECKVU_VM_OPTIONS = [
    "-XX:TieredStopAtLevel=1",
    "-Xms256m",
    "-Xmx512m",
    "-XX:+UseSerialGC",
]


def build_command(java, jar, project_file, user_path=None,
                  controller_properties=None, load_generator_properties=None,
                  app_proxy=None, app_proxy_username=None, app_proxy_bypass=None,
                  output=None, work_dir=None, keep_temp_work_dir=False):
    command = [java] + CHECKVU_VM_OPTIONS + ["-jar", jar]
    if user_path:
        command.extend(["--user-path", user_path])
    if controller_properties:
        command.extend(["--controller-properties", controller_properties])
    if load_generator_properties:
        command.extend(["--load-generator-properties", load_generator_properties])
    if app_proxy:
        command.extend(["--app-proxy", app_proxy])
    if app_proxy_username:
        command.extend(["--app-proxy-username", app_proxy_username])
    if app_proxy_bypass:
        command.extend(["--app-proxy-bypass", app_proxy_bypass])
    if output:
        command.extend(["--output", output])
    if work_dir:
        command.extend(["--work-dir", work_dir])
    if keep_temp_work_dir:
        command.append("--keep-temp-work-dir")
    command.append(project_file)
    return command


def run_checkvu(command):
    """Run the JAR, inheriting stdio so the CLI output is the JAR output, and return its exit code."""
    sys.stdout.flush()
    sys.stderr.flush()
    # Emptied so it cannot override CHECKVU_VM_OPTIONS nor reach the Load Generator child.
    env = dict(os.environ, JAVA_TOOL_OPTIONS="")
    try:
        completed = subprocess.run(command, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin, env=env)
    except OSError as err:
        raise cli_exception.CliException("Failed to run CheckVU: {0}".format(str(err)))
    return completed.returncode
