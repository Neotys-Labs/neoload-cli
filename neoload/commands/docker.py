import sys
import click

from neoload_cli_lib import user_data, tools
from commands import test_settings
from neoload_cli_lib.tools import upgrade_logging,downgrade_logging

import docker
import random
import traceback
import platform
from datetime import datetime
import time
import logging
import json
import socket
from urllib.parse import urlparse


key_container_naming_prefix = "neoload_cli"
auto_remove_containers = True
max_container_readiness_wait_sec = 60

key_meta_prior_docker = 'prior_docker'
key_spun_at_run = 'spun_at_run'
key_docker_run_id = 'run_id'


@click.command()
@click.argument("command", required=True, type=click.Choice(['prepare','attach', 'detach', 'forget', 'verify']))
@click.option('--tag', default="latest", help="The docker image version to use")
@click.option('--ctrlimage', default="neotys/neoload-controller", help="The controller image to use")
@click.option('--lgimage', default="neotys/neoload-loadgenerator", help="The load generator image to use")
@click.option('--all', is_flag=True, help="Apply this action to all resources")
@click.option('--nowait', is_flag=True, help="Do not wait for controller andxf load generator logs to indicate attach success")
@click.option('--addhosts', default=None, help="Hosts to add to the /etc/hosts file of the containers")
def cli(command, tag, ctrlimage, lgimage, all, nowait, addhosts):
    """Use local Docker to BYO infrastructure for a test.
    This uses the local Docker daemon to spin up containers to be used as infrastucture for the current test.
    NOTE: this feature is not supported by NeoLoad since your own Docker configuration is out-of-scope for support."""

    if command == "prepare":
        check_docker_system()

        set_prior_docker_attributes(tag,ctrlimage,lgimage,addhosts)

    elif command == "attach":
        check_docker_system()

        if test_settings.is_current_test_settings_set():
            upgrade_logging()
            derived = derive_docker_attributes(tag,ctrlimage,lgimage,addhosts)
            attach(explicit=True,
                tag=derived['tag'], ctrlimage=derived['ctrlimage'], lgimage=derived['lgimage'], addhosts=derived['addhosts'],
                wait_for_readiness=(not nowait))
            downgrade_logging()
        else:
            tools.system_exit({'message': 'No current test settings set. Please login and select a test before attaching.', 'code': 3})

    elif command == "detach":
        check_docker_system()
        upgrade_logging()
        askmode = sys.stdin.isatty()
        detach_infra(explicit=askmode, all=all)
        downgrade_logging()

    elif command == "forget":
        if has_prior_attach():
            detach_infra(explicit=False, all=True)
        user_data.set_meta(key_meta_prior_docker,None)

    elif command == "verify":
        check_docker_system()
        print_docker_system_status()

def check_docker_system():
    result = try_docker_system()

    if not result['success']:
        if 'connection refused' in result['logs'].lower():
            msg = "Docker installed, but connection to dockerd failed."
        else:
            msg = "Docker-specific error: " + result['logs']

        tools.system_exit({'message': msg, 'code': 2})

def print_docker_system_status():
    upgrade_logging()
    try:
        client = docker.from_env()
        infos = client.info()

        logging.debug(json.dumps(infos, indent=1))

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logging.error("Unexpected error from 'print_docker_system_status': "  + repr(traceback.format_exception(exc_type, exc_value,
                                          exc_traceback)))
    downgrade_logging()

def try_docker_system():
    result = {
        'success': False,
        'logs': "",
        'nopermission': False
    }
    preempt_msg = "Unexpected error in 'try_docker_system':"
    try:
        client = docker.from_env()
        preempt_msg = "Could not ping the Docker host."
        client.ping()

        preempt_msg = "Could not obtain version info from the Docker host."
        client.version()

        preempt_msg = "Could not list containers on the Docker host."
        client.containers.list()

        result['success'] = True

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        full_msg = preempt_msg  + repr(traceback.format_exception(exc_type, exc_value,
                                          exc_traceback))
        if 'connectionerror' in full_msg.lower() and 'permission denied' in full_msg.lower():
            result['nopermission'] = True
            result['logs'] = preempt_msg + " Do you have rights (i.e. sudo first)?"
        else:
            result['logs'] = full_msg

    return result


def has_prior_attach():
    prior = user_data.get_meta(key_meta_prior_docker)
    return (prior is not None)



def is_prior_attach_running(run_id):
    try:
        client = docker.from_env()
        filters = {
            'label': 'neoload-cli=' + run_id
        }
        networks = client.networks.list(
            filters = filters,
        )
        return len(networks) > 0
    except Exception:
        return False



def resume_prior_attach():
    prior = user_data.get_meta(key_meta_prior_docker)
    if has_prior_attach() and not (key_docker_run_id in prior and is_prior_attach_running(prior[key_docker_run_id])):
        # if no permissions to docker, don't bother trying, warn
        trial = try_docker_system()
        if trial['nopermission']:
            return False

        upgrade_logging()
        logging.info("Attaching based on prior Docker attach...")
        prior[key_spun_at_run] = True
        user_data.set_meta(key_meta_prior_docker, prior)
        attach(explicit=False,
            tag=prior['tag'], ctrlimage=prior['ctrlimage'], lgimage=prior['lgimage'], addhosts=prior['addhosts'],
            wait_for_readiness=True)
        downgrade_logging()
        return True

    return False


def cleanup_after_test():
    prior = user_data.get_meta(key_meta_prior_docker)
    logging.debug("has_prior_attach() = " + str(has_prior_attach()))
    if has_prior_attach() and (prior is not None and key_spun_at_run in prior and prior[key_spun_at_run] == True):
        logging.info("Detatching after spun at run")
        detach_infra(explicit=False, all=False)
        downgrade_logging()



def attach(explicit, tag, ctrlimage, lgimage, addhosts, wait_for_readiness):
    is_ready = False

    client = docker.from_env()

    json = test_settings.get_current_test_settings_json()

    container_ids = []
    lg_container_ids = []
    ctrl_container_id = None
    network_id = None

    run_id = str(random.randint(1,65535))
    port_range_start = random.randint(171,471)*100 # between 17100 and 47100
    rand_subnet_dot_two = random.randint(50,250)

    network_name = key_container_naming_prefix + run_id + "_network"
    subnet_first_three = "172."+str(rand_subnet_dot_two)+".0"

    labelsall = {
        'neoload-cli': run_id
    }

    commonenv = {
        "NEOLOADWEB_URL": user_data.get_user_data().get_url(),
        "NEOLOADWEB_TOKEN": user_data.get_user_data().get_token()
    }

    volumes = {}
    #TODO (if interactive mode and in debub mode at the same time)    volumes[os.getcwd()] = {'bind': '/launch', 'mode': 'ro'}

    core_constructs = {
        'docker': client,
        'network_name': network_name,
        'labelsall': labelsall,
        'volumes': volumes,
        'run_id': run_id,
        'commonenv': commonenv,
        'addhosts': addhosts
    }

    try:
        #TODO: add check if images don't exist locally yet, and pull along with proper logging.info() notifications
        pull_if_needed(lgimage,tag)
        pull_if_needed(ctrlimage,tag)

        network = setup_network(core_constructs, subnet_first_three)

        network_id = network.id

        base_ipx = 2
        lgs_spec = json['lgZoneIds']
        lg_index = 0
        for zone in lgs_spec:
            num_of_lgs = lgs_spec[zone]

            for x in range(num_of_lgs):
                lg = setup_lg(core_constructs, zone, lg_index, subnet_first_three, base_ipx, port_range_start, lgimage+":"+tag)

                container_ids.append(lg.id)
                lg_container_ids.append(lg.id)
                logging.info("Created load generator " + str(lg_index+1) + ".")

                network.connect(
                    container=lg.id,
                    ipv4_address=lg.name # always name the container the IP address (resolve cross-platform Docker DNS issues)
                )
                logging.info("Attached load generator " + str(x+1) + " to network.")

                base_ipx += 1

                lg_index += 1


        ctrl = setup_ctrl(core_constructs, json['controllerZoneId'], ctrlimage+":"+tag)
        container_ids.append(ctrl.id)
        ctrl_container_id = ctrl.id

        waiting_success = False

        logging.info("wait_for_readiness: " + str(wait_for_readiness))

        if wait_for_readiness:
            logging.info("Waiting for docker containers to be attached and ready.")

            waiting_success = wait_for_all_containers(ctrl_container_id,lg_container_ids)

            time.sleep( 1 ) # give a few moments for platform to recognize resources as available
        else:
            time.sleep( 1 ) # give a few moments for platform to recognize resources as available
            waiting_success = True

        if waiting_success:
            logging.info("All containers are attached" + (" and ready for use" if wait_for_readiness else "") + ".")
        else:
            tools.system_exit({'message': 'Could not verify that Docker containers were ready and attached.', 'code': 2})

        prior = set_prior_docker_attributes(tag,ctrlimage,lgimage,addhosts)

        prior[key_docker_run_id] = run_id
        prior[key_spun_at_run] = not explicit
        user_data.set_meta(key_meta_prior_docker, prior)

        is_ready = True

    except Exception:
        logging.error("Unexpected error in 'attach':", sys.exc_info()[0])

    prior = {
        "is_ready": is_ready,
        "network_id": network_id
    }
    prior[key_docker_run_id] = run_id

def create_default_docker_attributes(tag,ctrlimage,lgimage,addhosts):
    datas = {
        "tag": "latest" if tag is None else tag,
        "ctrlimage": "neotys/neoload-controller" if ctrlimage is None else ctrlimage,
        "lgimage": "neotys/neoload-loadgenerator" if lgimage is None else lgimage,
        "addhosts": addhosts
    }
    return datas

def derive_docker_attributes(tag,ctrlimage,lgimage,addhosts):
    datas = create_default_docker_attributes(tag,ctrlimage,lgimage,addhosts)

    prior = user_data.get_meta(key_meta_prior_docker)
    if prior is None:
        return datas

    for key in datas:
        if key in prior and prior[key] is not None:
            datas[key] = prior[key]
    return datas

def set_prior_docker_attributes(tag,ctrlimage,lgimage,addhosts):
    current = create_default_docker_attributes(tag,ctrlimage,lgimage,addhosts)
    user_data.set_meta(key_meta_prior_docker, current)
    return current

def pull_if_needed(image_name, tag):
    full_spec = image_name + ":" + tag

    logging.info("Checking for image [" + full_spec + "]")
    client = docker.from_env()

    local_image_id = None

    try:
        image = client.images.get(full_spec)
        local_image_id = image.short_id
        logging.info("Using local image [" + full_spec + "]")
    except docker.errors.ImageNotFound:
        local_image_id = None

    if local_image_id is None:
        logging.info("Pulling [" + full_spec + "]")
        #run_command("docker pull " + full_spec)
        image = client.images.pull(image_name, tag)
        image = client.images.get(full_spec)
        local_image_id = image.short_id

    logging.info("Satisfied need for image [" + full_spec + "]")



# def run_command(command):
#     cmd = ['ls', '-l', '/']
#     proc = subprocess.Popen(
#         shlex.split(command),
#         stdout=subprocess.PIPE,
#         stderr=subprocess.STDOUT,
#         # Make all end-of-lines '\n'
#         universal_newlines=True,
#     )
#     for line in unbuffered(proc):
#         print(line)
#
#     rc = proc.poll()
#     return rc
#
# # Unix, Windows and old Macintosh end-of-line
# newlines = ['\n', '\r\n', '\r']
# def unbuffered(proc, stream='stdout'):
#     stream = getattr(proc, stream)
#     with contextlib.closing(stream):
#         while True:
#             out = []
#             last = stream.read(1)
#             # Don't loop forever
#             if last == '' and proc.poll() is not None:
#                 break
#             while last not in newlines:
#                 # Don't loop forever
#                 if last == '' and proc.poll() is not None:
#                     break
#                 out.append(last)
#                 last = stream.read(1)
#             out = ''.join(out)
#             yield out

def setup_network(core_constructs, subnet_first_three):
    network = core_constructs['docker'].networks.create(
        name = core_constructs['network_name'],
        driver = "bridge",
        attachable = True,
        labels = core_constructs['labelsall'],
        ipam = docker.types.IPAMConfig(
            driver = 'default',
            pool_configs=[docker.types.IPAMPool(
                subnet = subnet_first_three+'.0/16',
                iprange = subnet_first_three+'.0/24',
                gateway = subnet_first_three+'.254'
            )]
        )
    )
    logging.info("Created docker network '" + core_constructs['network_name'] + "'")
    logging.debug(network.attrs)
    return network


def setup_lg(core_constructs, zone, lg_index, subnet_first_three, base_ipx, port_range_start, lgimage):

    lgport = port_range_start+lg_index
    lghost = subnet_first_three+"."+str(base_ipx)

    lg2ctrl_port = lgport
    # some Docker environments (like Windows vs. linux/mac) map ports differently
    # apparently on Windows systems, you must map to the dynamic port
    # whereas on linux/Mac, you would route to the default port
    if platform.system().lower() != 'windows':
        lg2ctrl_port = 7100

    hostandport = {
        "LG_HOST": lghost,
        "LG_PORT": lg2ctrl_port,
        "AGENT_SERVER_PORT": lg2ctrl_port
    }
    lgenv = core_constructs['commonenv'].copy()
    lgenv.update(hostandport)
    lgenv["ZONE"] = zone

    logging.info("Attaching load generator " + str(lg_index+1) + " '" + lgimage + "'.")

    portspec = {}
    portspec[""+str(lgport)+"/tcp"] = lgport

    container = core_constructs['docker'].containers.run(
        image=lgimage,
        name = lghost,
        labels = core_constructs['labelsall'],
        detach=True,
        extra_hosts=parse_extra_hosts(core_constructs['addhosts']),
        auto_remove=auto_remove_containers,
        environment=lgenv,
        volumes=core_constructs['volumes'],
        ports=portspec,
    )
    logging.info("Attaced load generator successfully.")
    return container


def setup_ctrl(core_constructs, zone, ctrlimage):

    ctrlenv = {
        "MODE": "Managed",
        "LEASE_SERVER": "NLWEB",
    }
    ctrlenv.update(core_constructs['commonenv'])
    ctrlenv["ZONE"] = zone

    logging.info("Attaching controller '" + ctrlimage + "'.")

    container = core_constructs['docker'].containers.run(
        image=ctrlimage,
        name = key_container_naming_prefix + core_constructs['run_id'] + "_ctrl",
        network = core_constructs['network_name'],
        labels = core_constructs['labelsall'],
        detach=True,
        extra_hosts=parse_extra_hosts(core_constructs['addhosts']),
        auto_remove=auto_remove_containers,
        environment=ctrlenv,
        volumes=core_constructs['volumes']
    )
    logging.info("Attaced controller successfully.")
    return container

def parse_extra_hosts(hosts_spec):
    dict = get_default_hosts_dns()
    logging.debug(json.dumps(dict))

    if not (hosts_spec is not None and len((hosts_spec+"").strip()) > 0):
        return dict

    hosts = hosts_spec.split(';')
    for host_pair in hosts:
        host_parts = host_pair.split('=')
        ip = None
        host = host_parts[0]
        if len(host_parts)==1:
            if host == 'null':
                continue
            logging.info("Resolving host [" + host + "]")
            ip = socket.gethostbyname(host)
        else:
            ip = host_parts[1]
        dict[host] = ip

    if len(dict)>0:
        logging.info("Added hosts: " + json.dumps(dict, indent=1))

    return dict

def get_default_hosts_dns():
    dict = {}
    urls = []
    urls.append(user_data.get_user_data().get_url())
    urls.append(user_data.get_user_data().get_file_storage_url())
    urls.append(user_data.get_user_data().get_frontend_url())
    for url in urls:
        parsed = urlparse(url)
        host = parsed.hostname
        if not validate_ip(host):
            logging.info("Resolving host [" + host + "] from URL: " + url)
            dict[host] = socket.gethostbyname(host)

    return dict


def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True


def wait_for_all_containers(ctrl_container_id,lg_container_ids):
    waiting_success = False

    for container_id in lg_container_ids:
        waiting_success = wait_for_logs_to_include(container_id,
            "Agent started|Connection test to Neoload Web successful",
            "Connection test to NeoLoad Web failed|The provided zone identifier is not valid")
        if not waiting_success:
            logging.warning("Couldn't ensure load generator readiness for " + container_id)
            break

    if ctrl_container_id is not None:
        waiting_success = wait_for_logs_to_include(ctrl_container_id,
            "Successfully connected to URL",
            "Connection test to NeoLoad Web failed|The provided zone identifier is not valid")
        if not waiting_success:
            logging.warning("Couldn't ensure controller readiness for " + container_id)

    return waiting_success

def wait_for_logs_to_include(container_id, str_to_find, str_to_fail):
    client = docker.from_env()
    wait_sec = 0
    started_at = datetime.now()
    strs_to_find = str_to_find.split("|")
    strs_to_fail = str_to_fail.split("|")
    logstr = ""
    found_failure = False
    has_exception = False
    looped_once = False

    try:
        container = client.containers.get(container_id)
        logging.info("Waiting for container " + container.name + " logs to indicate attachment readiness")

        while wait_sec < max_container_readiness_wait_sec:
            looped_once = True
            time.sleep(1)
            wait_sec = (datetime.now() - started_at).total_seconds()

            logstr = parse_container_logs_to_string(container)

            if contains_any(logstr, strs_to_find):
                return True

            if contains_any(logstr, strs_to_fail):
                logging.info("Found failure criteria")
                found_failure = True
                break

        if wait_sec >= max_container_readiness_wait_sec:
            logging.warning("Waited for container readiness for max time of " + str(max_container_readiness_wait_sec) + " seconds before defaulting.")
        else:
            logging.info("Exited waiting after " + str(wait_sec) + " seconds.")

        logging.debug("Timed out while waiting for "+container.name+" readiness.")

    except docker.Errors.NotFound:
        has_exception = not looped_once # This is okay if the container exiting caused a NotFound after being found
    except Exception:
        has_exception = True
        logging.error("Unexpected error in 'wait_for_logs_to_include':", sys.exc_info()[0])

    logging.warning("Container logs:\n"+logstr)

    return not (found_failure or has_exception) # unlike immediate success return True, async returns True if no errors

def contains_any(str_to_search, phrases):
    for s in phrases:
        if s.lower() in str_to_search.lower():
            return True
    return False

def parse_container_logs_to_string(container):
    logstr = container.logs()
    if logstr is None:
        logstr = ""
    else:
        logstr = logstr.decode("utf-8")
    return logstr

def detach_infra(explicit, all):
    client = docker.from_env()

    if explicit:
        upgrade_logging()

    filters = {
        'label': 'neoload-cli'
    }
    if not all:
        prior = user_data.get_meta(key_meta_prior_docker)
        if prior is not None and key_docker_run_id in prior:
            filters = {
                'label': 'neoload-cli=' + prior[key_docker_run_id]
            }
        else:
            logging.info('No prior Docker attach info, so nothing to do without --all argument')
            return # nothing to do, so bail

    containers = client.containers.list(
        all = True,
        filters = filters,
    )
    networks = client.networks.list(
        filters = filters,
    )
    before_count = len(containers) + len(networks)
    if before_count < 1:
        logging.info("No containers or networks with 'neoload-cli' label to delete.")
        return True # nothing to do, so bail

    logging.info("Containers:\n\t" + "\n\t".join(map(lambda x: x.name, containers)))
    logging.info("Networks:\n\t" + "\n\t".join(map(lambda x: x.name, networks)))

    do_it = 'n'
    if not explicit:
        do_it = 'y'
    elif sys.stdin.isatty():
        do_it = click.prompt("Are you sure you want to delete all containers and networks with the label '" + filters['label'] + "'? (y/n)", 'n', False)

    if not do_it == 'y':
        return True # user exited, so bail

    for container in containers:
        remove_container(client,container.id)

    for network in networks:
        remove_network(client,network.id)

    logging.info("All containers and networks with label [" + filters['label'] + "] removed.")


    containers = client.containers.list(
        all = True,
        filters = filters,
    )
    networks = client.networks.list(
        filters = filters,
    )

    after_count = len(containers) + len(networks)

    logging.info(str(after_count)+" docker artifacts with label=neoload-cli exist.")

    prior = user_data.get_meta(key_meta_prior_docker)
    if not prior is None:
        prior.pop(key_docker_run_id, None)
        user_data.set_meta(key_meta_prior_docker, prior)

    if explicit:
        downgrade_logging()

    return before_count > 0 and after_count < 1



def remove_container(client,container_id):
    try:
        container = client.containers.get(container_id)

        logging.debug("Container " + container.name + " logs:")
        #TODO preserve logs? # logging.debug(container.logs().decode("utf-8"))

        logging.info("Stopping container " + container.name)
        container.stop()
        if not auto_remove_containers:
            container.remove()

    except Exception:
        if "No such container" in str(sys.exc_info()[0]):
            logging.warning("Tried to remove non-existent container: " + container_id)
        else:
            logging.error("Unexpected error in 'remove_container':", sys.exc_info()[0])




def remove_network(client,network_id):
    logging.info("Removing network " + network_id)
    try:
        network = client.networks.get(network_id)
        network.remove()
        logging.info("Removed network " + network_id)
    except Exception:
        logging.error("Unexpected error in 'remove_network':", sys.exc_info()[0])
