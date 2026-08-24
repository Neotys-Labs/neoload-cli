import os
import platform
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlencode, urlparse

import requests

from neoload_cli_lib import cli_exception, paths

MIN_JAVA_VERSION = 21

# Public download goes through www.neotys.com/redirect.php (same contract as
# NeoLoad installer direct-download). CheckVU is not a CDN URL.
REDIRECT_BASE_URL = "https://www.neotys.com/redirect/redirect.php"
REDIRECT_PRODUCT = "checkvu"
REDIRECT_TARGET = "direct-download"
REDIRECT_FORMAT = "jar"
REDIRECT_VERSION = "latest"

# `os` query values match the CheckVU JAR filename suffixes.
OS_LINUX = "linux"
OS_LINUX_ARM64 = "linux-arm64"
OS_MAC = "mac"
OS_MAC_ARM64 = "mac_arm64"
OS_WIN32_X64 = "win32_x64"
SUPPORTED_OS = (OS_LINUX, OS_LINUX_ARM64, OS_MAC, OS_MAC_ARM64, OS_WIN32_X64)

CACHE_DIR_NAME = "checkvu"
FALLBACK_JAR_NAME = "checkvu.jar"

__java_version_pattern = re.compile(r'version "(\d+)(?:\.(\d+))?')
__content_disposition_filename = re.compile(
    r"filename\*?=(?:UTF-8\'\')?\"?([^\";]+)\"?", re.IGNORECASE)
__jar_version_pattern = re.compile(r"checkvu_(\d+)_(\d+)_(\d+)_", re.IGNORECASE)
__arm_machines = ("arm64", "aarch64")
__x64_machines = ("x86_64", "amd64", "x64")


def get_cache_dir():
    return os.path.join(paths.get_config_dir(), CACHE_DIR_NAME)


def list_cached_jars(cache_dir=None):
    cache_dir = cache_dir or get_cache_dir()
    if not os.path.isdir(cache_dir):
        return []
    return [os.path.join(cache_dir, name) for name in sorted(os.listdir(cache_dir))
            if name.lower().endswith(".jar") and os.path.isfile(os.path.join(cache_dir, name))]


def get_cached_jar_path():
    jars = list_cached_jars()
    if len(jars) == 1:
        return jars[0]
    return None


def detect_os(system=None, machine=None):
    """Map the host OS/arch to one of the five CheckVU JAR platforms."""
    system = (system if system is not None else platform.system()).lower()
    machine = (machine if machine is not None else platform.machine()).lower()
    is_arm = machine in __arm_machines
    is_x64 = machine in __x64_machines

    if system == "linux":
        if is_arm:
            return OS_LINUX_ARM64
        if is_x64:
            return OS_LINUX
    elif system == "darwin":
        if is_arm:
            return OS_MAC_ARM64
        return OS_MAC
    elif system.startswith("win"):
        if is_arm:
            raise cli_exception.CliException(
                "CheckVU has no Windows ARM JAR. Supported platform: {0}.".format(OS_WIN32_X64))
        return OS_WIN32_X64

    raise cli_exception.CliException(
        "Unsupported platform for CheckVU: {0} ({1}). Supported os values: {2}.".format(
            system, machine, ", ".join(SUPPORTED_OS)))


def build_redirect_url(os_name=None, version=REDIRECT_VERSION):
    """Build the redirect.php URL for the latest CheckVU JAR of this platform.

    Same query shape as NeoLoad installer direct-download, with CheckVU values:

        product=checkvu
        target=direct-download
        os=linux|linux-arm64|mac|mac_arm64|win32_x64
        version=latest
        format=jar

    `os` matches the delivered JAR suffix (checkvu_<ver>_<os>.jar).
    `version=latest` is resolved server-side; the CLI never pins a NeoLoad version.
    """
    if os_name is None:
        os_name = detect_os()
    query = urlencode([
        ("product", REDIRECT_PRODUCT),
        ("target", REDIRECT_TARGET),
        ("os", os_name),
        ("version", version),
        ("format", REDIRECT_FORMAT),
    ])
    return REDIRECT_BASE_URL + "?" + query


def version_from_filename(filename):
    """Read CheckVU version from a delivered filename such as checkvu_2026_3_0_linux.jar."""
    match = __jar_version_pattern.search(os.path.basename(filename))
    if match is None:
        return None
    return "{0}.{1}.{2}".format(match.group(1), match.group(2), match.group(3))


def filename_from_response(response, fallback=FALLBACK_JAR_NAME):
    cd = response.headers.get("Content-Disposition") or ""
    match = __content_disposition_filename.search(cd)
    if match:
        name = os.path.basename(unquote(match.group(1).strip()))
        if name:
            return name
    path = urlparse(response.url).path
    name = os.path.basename(unquote(path))
    if name.lower().endswith(".jar"):
        return name
    return fallback


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
    return spec is not None and "://" in spec


def resolve_jar(engine_jar=None, ssl_cert=""):
    """Resolves the CheckVU fat JAR.

    Resolution order:
      1. --jar / --engine-jar local file: skip download, run that JAR (hotfix).
      2. --jar / --engine-jar URL: download that URL into the cache (1 JAR).
      3. redirect.php latest for this OS: follow redirect, cache 1 JAR, replace older.
    """
    if engine_jar:
        if is_url(engine_jar):
            return download_jar(engine_jar, ssl_cert)
        if not os.path.isfile(engine_jar):
            raise cli_exception.CliException("CheckVU JAR not found at '{0}'.".format(engine_jar))
        return engine_jar

    return download_jar(build_redirect_url(), ssl_cert)


def _keep_only_jar(cache_dir, keep_path):
    keep_path = os.path.abspath(keep_path)
    for path in list_cached_jars(cache_dir):
        if os.path.abspath(path) != keep_path:
            os.remove(path)


def _is_jar_file(path):
    try:
        with open(path, "rb") as stream:
            return stream.read(2) == b"PK"
    except OSError:
        return False


def download_jar(url, ssl_cert=""):
    """Download the latest CheckVU JAR through redirect.php, cache a single file.

    Follows HTTP redirects. If the cache already holds the redirected filename
    (same version), the body is not fetched again. Any other cached JAR is removed.
    """
    from tqdm import tqdm
    from neoload_cli_lib import tools

    verify = tools.ssl_cert_to_verify(ssl_cert)
    cache_dir = get_cache_dir()
    os.makedirs(cache_dir, exist_ok=True)
    partial_destination = None
    try:
        with requests.get(url, stream=True, verify=verify, allow_redirects=True) as response:
            response.raise_for_status()
            filename = filename_from_response(response)
            destination = os.path.join(cache_dir, filename)
            if os.path.isfile(destination) and _is_jar_file(destination):
                _keep_only_jar(cache_dir, destination)
                return destination

            print("Downloading CheckVU JAR from " + url + "\n")
            total_bytes = int(response.headers.get("content-length", 0))
            progress_bar = None
            if tools.is_user_interactive():
                progress_bar = tqdm(desc=filename, total=total_bytes, unit="B",
                                    unit_scale=True, leave=False, dynamic_ncols=True)
            partial_destination = destination + ".part"
            with open(partial_destination, "wb") as stream:
                for chunk in response.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        stream.write(chunk)
                        if progress_bar is not None:
                            progress_bar.update(len(chunk))
            if progress_bar is not None:
                progress_bar.close()
        os.replace(partial_destination, destination)
        partial_destination = None
        if not _is_jar_file(destination):
            os.remove(destination)
            raise cli_exception.CliException(
                "The CheckVU download from '{0}' did not return a JAR.".format(url))
        _keep_only_jar(cache_dir, destination)
        return destination
    except cli_exception.CliException:
        raise
    except Exception as err:
        raise cli_exception.CliException(
            "Failed to download the CheckVU JAR from '{0}':\n{1}".format(url, str(err)))
    finally:
        if partial_destination and os.path.isfile(partial_destination):
            os.remove(partial_destination)


def build_command(java, jar, project_file, user_path=None,
                  controller_properties=None, load_generator_properties=None,
                  app_proxy=None, app_proxy_username=None, app_proxy_bypass=None,
                  work_dir=None, keep_temp_work_dir=False):
    command = [java, "-jar", jar]
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
    try:
        completed = subprocess.run(command, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin)
    except OSError as err:
        raise cli_exception.CliException("Failed to run CheckVU: {0}".format(str(err)))
    return completed.returncode
