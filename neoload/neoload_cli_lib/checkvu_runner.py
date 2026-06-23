import os
import re
import shutil
import subprocess
import sys

from neoload_cli_lib import cli_exception, paths

MIN_JAVA_VERSION = 21

# Default download URL pointing at the "latest" CheckVU JAR
# TODO: set this once we have public jar url
# use --jar-path or --jar-url for now
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

# TODO cache invalidation according to project version ?
def resolve_jar(jar_path=None, jar_url=None, ssl_cert=''):
    """Resolves the CheckVU fat JAR.
    Resolution order:
      1. --jar-path (explicit local file)
      2. --jar-url (explicit download URL) -> download + cache
      3. cached JAR if exists
      4. DEFAULT_JAR_URL -> download + cache
      5. error
    """
    if jar_path:
        if not os.path.isfile(jar_path):
            raise cli_exception.CliException("CheckVU JAR not found at '{0}'.".format(jar_path))
        return jar_path

    cache_path = get_cached_jar_path()

    if jar_url:
        return download_jar(jar_url, cache_path, ssl_cert)

    if os.path.isfile(cache_path):
        return cache_path

    if DEFAULT_JAR_URL:
        return download_jar(DEFAULT_JAR_URL, cache_path, ssl_cert)

    raise cli_exception.CliException(
        "No CheckVU JAR available. Provide one with:\n"
        "  - --jar-path <path-to-neoload-checkvu-cli.jar>, or\n"
        "  - --jar-url <download-url>\n")


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


def build_command(java, jar, project, user_path=None):
    command = [java, "-jar", jar]
    if user_path:
        command.extend(["--user-path", user_path])
    command.append(project)
    return command


def run_checkvu(command):
    """Run the JAR, inheriting stdio so the CLI output is the JAR output, and return its exit code."""
    try:
        completed = subprocess.run(command, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin)
    except OSError as err:
        raise cli_exception.CliException("Failed to run CheckVU: {0}".format(str(err)))
    return completed.returncode
