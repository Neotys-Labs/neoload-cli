import os
import sys

import click

from neoload_cli_lib import checkvu_runner, cli_exception
import neoload_cli_lib.schema_validation as schema_validation
from neoload_cli_lib.schema_validation import __default_schema_url

__yaml_extensions = (".yaml", ".yml")

@click.command()
@click.option('--jar-path',
              help="Path to a locally built neoload-checkvu-cli JAR.  You can "
              "also provide --jar-url instead, if none are provided "
              "default jar url will be used, or cached jar if any",
              metavar="PATH")
@click.option('--jar-url',
              help="Download URL for the CheckVU JAR. This is "
                    "optional. You can also provide --jar-path instead, if none"
                    "are provided default jar url will be used, or cached jar"
                    "if any",
              metavar="URL")
@click.option('--java', help="Path to the java executable to use. "
                            "Defaults to JAVA_HOME/bin/java, then java on the PATH.", metavar="PATH")
@click.option('--user-path', help="Run only the specified user path. "
                                  "If omitted, all user paths are executed sequentially.", metavar="NAME")
@click.option('--schema-url', help="The URL (or local path) to the as-code schema. By default, use the one on Github",
              metavar="URL", default=__default_schema_url, show_default=True)
@click.option('--ssl-cert', default="",
              help="Path to SSL certificate or write False to disable certificate checking. "
                   "Used both for schema validation and the JAR download.")
@click.argument('project')
def cli(jar_path, jar_url, java, user_path, schema_url, ssl_cert, project):
    """Runs a CheckVU on an as-code PROJECT using the headless CheckVU JAR.
    PROJECT is a path to an as-code yaml file. A single virtual user is executed
    to verify the project runs."""
    if not project.lower().endswith(__yaml_extensions):
        raise cli_exception.CliException("Project file must be a yaml (\".yaml\", \".yml\") file: " + project)
    if not os.path.isfile(project):
        raise cli_exception.CliException("Project file not found: " + project)
    print(schema_validation.validate_path(project, schema_url, ssl_cert), flush=True)

    java_executable = checkvu_runner.resolve_java(java)
    checkvu_runner.check_java_version(java_executable)

    resolved_jar = checkvu_runner.resolve_jar(jar_path, jar_url, ssl_cert)

    command = checkvu_runner.build_command(java_executable, resolved_jar, project, user_path)
    exit_code = checkvu_runner.run_checkvu(command)
    sys.exit(exit_code)
