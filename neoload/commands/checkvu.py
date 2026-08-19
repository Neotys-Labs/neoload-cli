import os
import sys

import click

from neoload_cli_lib import checkvu_runner, cli_exception
import neoload_cli_lib.schema_validation as schema_validation
from neoload_cli_lib.schema_validation import __default_schema_url

__yaml_extensions = (".yaml", ".yml")

@click.command()
@click.option('-e', '--engine-jar',
              help="CheckVU engine JAR to run: a local file, for air-gapped or pinned setups, or a download URL. "
                   "Defaults to the cached JAR, otherwise the release URL for this version.",
              metavar="PATH|URL")
@click.option('-j', '--java', help="Path to the java executable to use. "
                            "Defaults to JAVA_HOME/bin/java, then java on the PATH.", metavar="PATH")
@click.option('-u', '--user-path', help="Run only the specified user path. If omitted, all user paths in the file "
                                  "are executed sequentially. An unknown name fails and lists the user paths "
                                  "found in the file.", metavar="NAME")
@click.option('-s', '--as-code-schema', default=__default_schema_url, show_default=True,
              help="NeoLoad as-code schema (URL or local path) to validate PROJECT_FILE "
                   "against. Defaults to the schema published for this release on Github.",
              metavar="PATH|URL")
@click.option('--ssl-cert', default="",
              help="Path to SSL certificate or write False to disable certificate checking. "
                   "Used both for schema validation and the JAR download.")
@click.option('--controller-properties',
              help="Advanced. Path to controller.properties file merged additively into the Controller "
                   "configuration; only the keys you set are overridden, other embedded values are kept.",
              metavar="PATH")
@click.option('--load-generator-properties',
              help="Advanced. Path to agent.properties file merged additively into the Load Generator "
                   "configuration; only the keys you set are overridden.",
              metavar="PATH")
@click.option('--app-proxy',
              help="Proxy used to reach the tested applications, as host:port (e.g. myproxy.corp:8080). "
                   "Applies to both HTTP and HTTPS application traffic (User Path validation / Load Generator "
                   "traffic). Not used for NeoLoad Web API calls. CheckVU CLI download proxy uses the standard "
                   "HTTPS_PROXY, HTTP_PROXY and NO_PROXY variables instead.",
              metavar="HOST:PORT")
@click.option('--app-proxy-username',
              help="Username for --app-proxy authentication (optional). The password is read from environment "
                   "variable NEOLOAD_CHECK_VU_APP_PROXY_PASSWORD; there is no flag for it, so it is never "
                   "exposed in the process list or CI logs.",
              metavar="USERNAME")
@click.option('--app-proxy-bypass',
              help="Comma-separated hosts that bypass --app-proxy (e.g. localhost,internal.corp).",
              metavar="HOSTS")
@click.option('-w', '--work-dir',
              help="Directory for engine scratch files and logs. Defaults to a temporary directory. "
                   "A directory you supply is never deleted.",
              metavar="PATH")
@click.option('--keep-temp-work-dir', is_flag=True, default=False,
              help="Keep the temporary work directory after the run instead of deleting it. "
                   "Equivalent to setting CHECKVU_CLI_KEEP_TEMP_WORK_DIR=1. "
                   "Has no effect when --work-dir is already set, since that directory is never auto-deleted.")
@click.argument('project_file')
def cli(engine_jar, java, user_path, as_code_schema, ssl_cert,
        controller_properties, load_generator_properties,
        app_proxy, app_proxy_username, app_proxy_bypass, work_dir, keep_temp_work_dir,
        project_file):
    """  Validate the User Paths of a NeoLoad as-code Project locally.

    Runs each User Path once against the application and reports whether
    it completes without blocking errors. This is not a load test: no
    Population, no Scenario, no Result. Exits 0 when every User Path passes, 1
    otherwise, and always writes a JSON output.

    PROJECT_FILE is the as-code Project YAML file. Its parent directory is the
    Project root; colocated assets such as CSV files must live under that
    root.
    """
    if not project_file.lower().endswith(__yaml_extensions):
        raise cli_exception.CliException("Project file must be a yaml (\".yaml\", \".yml\") file: " + project_file)
    if not os.path.isfile(project_file):
        raise cli_exception.CliException("Project file not found: " + project_file)
    print(schema_validation.validate_path(project_file, as_code_schema, ssl_cert), flush=True)

    java_executable = checkvu_runner.resolve_java(java)
    checkvu_runner.check_java_version(java_executable)

    resolved_jar = checkvu_runner.resolve_jar(engine_jar, ssl_cert)

    command = checkvu_runner.build_command(
        java_executable, resolved_jar, project_file,
        user_path=user_path,
        controller_properties=controller_properties,
        load_generator_properties=load_generator_properties,
        app_proxy=app_proxy,
        app_proxy_username=app_proxy_username,
        app_proxy_bypass=app_proxy_bypass,
        work_dir=work_dir,
        keep_temp_work_dir=keep_temp_work_dir,
    )
    exit_code = checkvu_runner.run_checkvu(command)
    sys.exit(exit_code)
