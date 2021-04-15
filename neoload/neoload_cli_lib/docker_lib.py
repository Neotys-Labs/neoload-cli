from neoload_cli_lib import user_data, tools, hooks, config_global, cli_exception
from commands import zones
import sys
import docker
import traceback
import logging
import re
import socket
import time

DOCKER_LAUNCHED = 'docker.launched'
DOCKER_ZONE = 'docker.zone'
DOCKER_LG_DEFAULT_COUNT = 'docker.lg.default_count'
DOCKER_LG_IMAGE = 'docker.lg.image'
DOCKER_CONTROLLER_DEFAULT_COUNT = 'docker.controller.default_count'
DOCKER_CONTROLLER_IMAGE = 'docker.controller.image'

HOOK_NAME_TEST_START = "test.start"
HOOK_TEST_START = "neoload_cli_lib.docker_lib.hook_test_start"
HOOK_NAME_TEST_STOP = "test.stop"
HOOK_TEST_STOP = "neoload_cli_lib.docker_lib.hook_test_stop"

default_settings = {
    DOCKER_CONTROLLER_IMAGE: 'neotys/neoload-controller:latest',
    DOCKER_CONTROLLER_DEFAULT_COUNT: 1,
    DOCKER_LG_IMAGE: 'neotys/neoload-loadgenerator:latest',
    DOCKER_LG_DEFAULT_COUNT: 2,
    DOCKER_ZONE: 'defaultzone',
    DOCKER_LAUNCHED: []
}

client=None


def get_docker_client():
    global client
    if not client:
        try:
            client = docker.from_env()
        except Exception:
            if cli_exception.CliException.is_debug():
                logging.exception("Exception occurs during docker client creation.")
            raise cli_exception.CliException("Exception occurs during docker client creation.")
    return client

def get_setting(key):
    return config_global.get_attr(key, default_settings.get(key))


def add_set(key, list_to_add):
    old_list = get_setting(key)
    config_global.set_attr(key, old_list + list_to_add)


def install():
    hooks.register(HOOK_NAME_TEST_START, HOOK_TEST_START)
    hooks.register(HOOK_NAME_TEST_STOP, HOOK_TEST_STOP)


def uninstall():
    hooks.unregister(HOOK_NAME_TEST_START, HOOK_TEST_START)
    hooks.unregister(HOOK_NAME_TEST_STOP, HOOK_TEST_STOP)


def status():
    installed = "installed" if hooks.is_registered(HOOK_NAME_TEST_START, HOOK_TEST_START) else "not installed"
    print("configuration:")

    for k in default_settings:
        print(k + " = " + str(get_setting(k)))

    print()
    print("docker hooks is " + installed)
    print()
    check_images(DOCKER_LG_IMAGE)
    check_images(DOCKER_CONTROLLER_IMAGE)

    check_docker()

    launched_container = get_setting(DOCKER_LAUNCHED)
    if launched_container:
        print("\ncontainers :")
        for c_id in launched_container:
            print(container_status(c_id))
    else:
        try:
            check_zone(get_setting(DOCKER_ZONE))
        except cli_exception.CliException as ex:
            print(str(ex))


def container_status(container_id):
    try:
        container = get_docker_client().containers.get(container_id)
        return container.name + ' [' + container.status + ']'
    except docker.errors.NotFound:
        return container_id + ' [NOT FOUND]'


def check_images(key):
    image_name = get_setting(key)
    image_status = " is not pulled" if len(get_docker_client().images.list(image_name)) == 0 else " is pulled"
    print("image " + image_name + image_status)


def up(no_wait):
    zone = get_setting(DOCKER_ZONE)
    check_zone(zone)
    start_infra(
        zone,
        int(get_setting(DOCKER_CONTROLLER_DEFAULT_COUNT)),
        int(get_setting(DOCKER_LG_DEFAULT_COUNT)),
        no_wait,
        'manual'
    )


def check_zone(zone_set):
    zone = get_zone(zone_set)
    if not zone:
        raise cli_exception.CliException("zone " + zone_set + " doesn't exist")
    if zone.get('type') != "STATIC":
        raise cli_exception.CliException("zone " + zone_set + " is not static !")
    if zone.get('controller'):
        raise cli_exception.CliException(
            "controller with " + zone_set + " zone is not empty. Try neoload docker clean")
    if zone.get('loadgenerators'):
        logging.warning("lg zone with " + zone_set + " is not empty. Try neoload docker clean")


def get_zone(zone_id):
    for zone in zones.get_zones():
        if zone.get('id') == zone_id:
            return zone
    return None


def down():
    stop_infra()


def compute_hosts(lg_containers):
    hosts = {}
    for lg_container in lg_containers:
        lg_container.reload()  # refresh data after launch.
        hosts[lg_container.name] = lg_container.attrs['NetworkSettings']['IPAddress']
    return hosts


def generate_conf_ctrl(zone, lg_containers):
    env = {"MODE": "Managed"}
    env.update(common_env(zone))
    return {
        'env': env,
        'name_prefix': 'ctrl',
        'hosts': compute_hosts(lg_containers)
    }


def generate_conf_lg(zone):
    return {
        'env': common_env(zone),
        'name_prefix': 'lg'
    }


def stop_infra():
    for container_id in get_setting(DOCKER_LAUNCHED):
        try:
            container = get_docker_client().containers.get(container_id)
            container.stop()
        except docker.errors.NotFound:
            pass
    forget()


def common_env(zone):
    return {
        "NEOLOADWEB_URL": user_data.get_user_data().get_url(),
        "NEOLOADWEB_TOKEN": user_data.get_user_data().get_token(),
        "ZONE": zone
    }


def launch_ctrl(count, zone, lg_containers, reason):
    image = pull_if_needed(get_setting(DOCKER_CONTROLLER_IMAGE))
    return start_container(image, generate_conf_ctrl(zone, lg_containers), count, reason)


def launch_lg(count, zone, reason):
    image = pull_if_needed(get_setting(DOCKER_LG_IMAGE))
    return start_container(image, generate_conf_lg(zone), count, reason)


def extract_number(prefix, element):
    num, number_match = re.subn("^" + prefix + "-([0-9]+)-.*$", r"\g<1>", element.name)
    return int(num) if number_match > 0 else 0


def max_number(prefix):
    containers_list = get_docker_client().containers.list(all=True)
    return max(map(lambda c: extract_number(prefix, c), containers_list)) if containers_list else 0


def start_container(image, configuration, count, reason):
    prefix = configuration.get('name_prefix')
    number = max_number(prefix)
    containers = []
    for i in range(count):
        name = prefix + '-' + str(number + i + 1) + '-' + socket.gethostname().lower()
        container = get_docker_client().containers.run(
            image=image.id,
            name=name,
            hostname=name,
            labels={'launched-by-neoload-cli': reason},
            detach=True,
            extra_hosts=configuration.get('hosts', {}),
            auto_remove=True,
            environment=configuration.get('env', {})
        )
        containers.append(container)
    return containers


def make_waiting(containers_name, zone):
    waiting_list = []
    names = list(map(lambda c: c['name'], zone.get('controllers') + zone.get('loadgenerators')))
    for c_name in containers_name:
        if c_name not in names:
            waiting_list.append(c_name)
    return waiting_list


def wait_is_up(containers, zone_id):
    containers_name = map(lambda c: c.name, containers)
    while True:
        time.sleep(5)
        waiting = make_waiting(containers_name, get_zone(zone_id))
        if waiting:
            print("Waiting: " + str(waiting))
        else:
            break


def start_infra(zone_id, ctrl_count: int, lg_count: int, no_wait, reason):
    containers = []
    try:
        containers = launch_lg(lg_count, zone_id, reason)
        containers += launch_ctrl(ctrl_count, zone_id, containers, reason)
        add_set(DOCKER_LAUNCHED, list(map(lambda c: c.id, containers)))
        if not no_wait:
            wait_is_up(containers, zone_id)
    except docker.errors.DockerException as ex:
        for container in containers:
            container.stop()
        logging.error("Unexpected error in 'attach':" + str(ex))


def extract_lg_number(test_settings_json, zone):
    number_lg = test_settings_json.get('lgZoneIds').get(zone)
    return number_lg if number_lg else 0


def hook_test_start(test_settings_json):
    zone = get_setting(DOCKER_ZONE)
    if test_settings_json.get('controllerZoneId') == zone:
        number_lg = extract_lg_number(test_settings_json, zone)
        zone_obj = get_zone(zone)
        if number_lg <= len(zone_obj.get('loadgenerators')) and 1 <= len(zone_obj.get('controllers')):
            print("zone is already up", file=sys.stderr)
            return

        print("Launch docker containers", file=sys.stderr)

        check_zone(zone)
        start_infra(
            zone,
            1,
            number_lg,
            False,
            test_settings_json.get('id')
        )


def hook_test_stop():
    print("Stop docker containers", file=sys.stderr)
    stop_infra()


def pull_if_needed(image_name):
    try:
        return get_docker_client().images.get(image_name)
    except docker.errors.ImageNotFound:
        print("Pulling [" + image_name + "]", file=sys.stderr)
        return get_docker_client().images.pull(image_name)


def check_docker():
    preempt_msg = "Unexpected error in 'try_docker_system':"
    try:
        preempt_msg = "Could not ping the Docker host."
        get_docker_client().ping()

        preempt_msg = "Could not obtain version info from the Docker host."
        get_docker_client().version()

        preempt_msg = "Could not list containers on the Docker host."
        get_docker_client().containers.list()

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        full_msg = preempt_msg + repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        lower = full_msg.lower()
        if 'connectionerror' in lower and 'permission denied' in lower:
            msg = preempt_msg + " Do you have rights (i.e. sudo first)?"
        elif 'connection refused' in lower:
            msg = "Docker installed, but connection to dockerd failed."
        else:
            msg = "Docker-specific error: " + full_msg

        tools.system_exit({'message': msg, 'code': 2})


def clean():
    list_to_clean = get_docker_client().containers.list(all=True, filters={'label': 'launched-by-neoload-cli'})
    for container in list_to_clean:
        container.stop()
    forget()


def kill():
    list_to_clean = get_docker_client().containers.list(all=True, filters={'label': 'launched-by-neoload-cli'})
    for container in list_to_clean:
        container.remove(force=True, v=True)
    forget()


def forget():
    config_global.set_attr(DOCKER_LAUNCHED, None)


def set_client(new_client):
    global client
    client = new_client
