import click

from neoload_cli_lib import docker_lib, rest_crud


@click.command()
@click.argument('command', required=True,
                type=click.Choice(['up', 'down', 'clean', 'forget', 'install', 'uninstall', 'status']))
@click.option('--no-wait', is_flag=True,
              help="Do not wait for controller and load generator in zones api", default=False)
def cli(command, no_wait):
    """\b
    Use local Docker to BYO infrastructure for a test.
    This uses the local Docker daemon to spin up containers to be used as infrastucture for the current test.
    Commands:
        - up/down: create or delete container depends of the configuration
        - forget: remove container from the launched list. That avoid to be removed with down command.
        - clean: remove all container created by neoload-cli even if it was forgotten.
        - install/uninstall: add/remove hooks on run command to up when the controller zone is same and zone is empty. Shut down at the end of test running.
        - status: display configuration and general status.

    \b
    configuration are :
        - docker.controller.image (default:  neotys/neoload-controller:latest)
        - docker.controller.default_count (default: 1)
        - docker.lg.image (default: neotys/neoload-loadgenerator:latest)
        - docker.lg.default_count (default: 2)
        - docker.zone

    \b
    NOTE: this feature is not supported by NeoLoad since your own Docker configuration is out-of-scope for support."""
    rest_crud.set_current_command()
    if command == "install":
        docker_lib.install()
    elif command == "uninstall":
        docker_lib.uninstall()
    elif command == "status":
        docker_lib.status()
    elif command == "up":
        docker_lib.up(no_wait)
    elif command == "down":
        docker_lib.down()
    elif command == "clean":
        docker_lib.clean()
    elif command == "forget":
        docker_lib.forget()
