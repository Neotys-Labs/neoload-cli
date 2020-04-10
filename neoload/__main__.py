import click
import os
import logging
import coloredlogs

from neoload_cli_lib import tools, rest_crud

plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')


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
        rest_crud.set_current_command(name)
        if os.path.isfile(fn):
            with open(fn) as f:
                code = compile(f.read(), fn, 'exec')
                eval(code, ns, ns)
            return ns['cli']
        else:
            logging.exception(name + " is not a neoload command")
            return None


@click.command(cls=NeoLoadCLI, help='', chain=True)
@click.option('--debug', default=False, is_flag=True)
@click.option('--batch', default=False, is_flag=True, help="Don't ask a confirmation")
@click.version_option('1.0.0')
def cli(debug, batch):
    if debug:
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    tools.set_batch(batch)
    coloredlogs.install(level=logging.getLogger().level)

if __name__ == '__main__':
    cli()
