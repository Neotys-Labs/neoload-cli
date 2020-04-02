import click
import os
import logging

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
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns['cli']

    # cli = NeoLoadCLI(help='', chain=True)


@click.command(cls=NeoLoadCLI, help='', chain=True)  # , chain=True
@click.option('--debug', default=False, is_flag=True)
@click.version_option('1.0.0')
def cli(debug):
    if debug:
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True


if __name__ == '__main__':
    cli()
