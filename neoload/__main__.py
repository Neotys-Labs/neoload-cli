import logging
import os
import sys

import click
import coloredlogs

from neoload_cli_lib import tools, cli_exception
from neoload_cli_lib.cli_exception import CliException

import urllib3

urllib3.disable_warnings()

plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')

# Disable output buffering.
sys.stdout = sys.__stdout__


class NeoLoadCLI(click.MultiCommand):
    def list_commands(self, ctx):
        """Dynamically get the list of commands."""
        rv = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith('.py') and not filename.startswith('__init__'):
                rv.append(filename[:-3].replace('_', '-'))
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        """Dynamically get the command."""
        ns = {}
        fn = os.path.join(plugin_folder, name.replace('-', '_') + '.py')
        if os.path.isfile(fn):
            with open(fn) as f:
                code = compile(f.read(), fn, 'exec')
                eval(code, ns, ns)
            return ns['cli']
        else:
            raise cli_exception.CliException("\"" + name + "\" is not a neoload command")


@click.command(cls=NeoLoadCLI, help='', chain=True)
@click.option('--debug', default=False, is_flag=True)
@click.option('--batch', default=False, is_flag=True, help="Don't ask a question or read stdin")
@click.version_option(tools.compute_version())
def cli(debug, batch):
    if debug:
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        cli_exception.CliException.set_debug(True)

    tools.set_batch(batch)
    if batch:
        sys.stdin = open(os.devnull, 'r')
    if tools.is_color_terminal():
        coloredlogs.install(level=logging.getLogger().level)


if __name__ == '__main__':
    try:
        cli()
    except CliException as ex:
        print(ex.format_message(), file=sys.stderr)
    except Exception as ex:
        if cli_exception.CliException.is_debug():
            raise ex
        else:
            print(ex.__str__(), file=sys.stderr)
