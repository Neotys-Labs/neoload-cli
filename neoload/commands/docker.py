import sys
import click

from neoload_cli_lib import user_data
from commands import test_settings

import docker
import random
import traceback
import platform
from datetime import datetime
import time
import logging
import coloredlogs


key_container_naming_prefix = "neoload_cli"
auto_remove_containers = True
max_container_readiness_wait_sec = 120

key_meta_prior_docker = 'prior_docker'
key_spun_at_run = 'spun_at_run'
key_docker_run_id = 'runId'

prior_logging_level = logging.NOTSET



@click.command()
@click.argument("command", required=True, type=click.Choice(['ls', 'attach', 'detach', 'forget']))
@click.option('--tag', default="latest", help="The docker image version to use")
@click.option('--ctrlimage', default="neotys/neoload-controller", help="The controller image to use")
@click.option('--lgimage', default="neotys/neoload-loadgenerator", help="The load generator image to use")
@click.option('--all', is_flag=True, help="Apply this action to all resources")
@click.option('--force', is_flag=True, help="Do not prompt/confirm")
def cli(command, tag, ctrlimage, lgimage, all, force):

    if command == "attach":
        upgrade_logging()
        attach(explicit=True, tag=tag, ctrlimage=ctrlimage, lgimage=lgimage)
    elif command == "detach":
        detach_all_infra(explicit=(not force), all=all)
    elif command == "forget":
        user_data.set_meta(key_meta_prior_docker,None)
    else:
        raise ValueError("Command '" + command + "' not yet implemented.")



def upgrade_logging():
    level = logging.getLogger().getEffectiveLevel()

    global prior_logging_level

    if(level > logging.INFO or level == logging.NOTSET):
        prior_logging_level = level
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.getLogger().setLevel(logging.INFO)
        coloredlogs.install(
            level=logging.getLogger().level,
            fmt='%(asctime)s,%(msecs)03d %(name)s[%(process)d] %(levelname)s %(message)s',
            datefmt='%H:%M:%S'
        )



def downgrade_logging():
    logging.getLogger().setLevel(prior_logging_level)
    coloredlogs.install(level=logging.getLogger().level)



def has_prior_attach():
    prior = user_data.get_meta(key_meta_prior_docker)
    return (prior is not None)



def is_prior_attach_running(runId):
    try:
        client = docker.from_env()
        filters = {
            'label': 'neoload-cli=' + runId
        }
        networks = client.networks.list(
            filters = filters,
        )
        return len(networks) > 0
    except Exception as err:
        return False



def resume_prior_attach():
    prior = user_data.get_meta(key_meta_prior_docker)
    if has_prior_attach():
        if not (key_docker_run_id in prior and is_prior_attach_running(prior[key_docker_run_id])):
            upgrade_logging()
            logging.info("Attaching based on prior Docker attach...")
            prior[key_spun_at_run] = True
            user_data.set_meta(key_meta_prior_docker, prior)
            attach(explicit=False, tag=prior['tag'], ctrlimage=prior['ctrlimage'], lgimage=prior['lgimage'])
            return True

    return False



def cleanup_after_test():
    prior = user_data.get_meta(key_meta_prior_docker)
    logging.debug("has_prior_attach() = " + str(has_prior_attach()))
    if has_prior_attach() and (prior is not None and key_spun_at_run in prior and prior[key_spun_at_run] == True):
        logging.info("Detatching after spun at run")
        detach_all_infra(explicit=False, all=False)
        downgrade_logging()



def attach(explicit, tag, ctrlimage, lgimage):
    isReady = False

    client = docker.from_env()

    numOfLGs = 1
    json = test_settings.get_current_test_settings_json()

    container_ids = []
    lg_container_ids = []
    ctrl_container_id = None
    network_id = None

    runId = str(random.randint(1,65535))
    randPortRange = random.randint(171,471)*100 # between 17100 and 47100
    randSubnet2 = random.randint(50,250)

    networkName = key_container_naming_prefix + runId + "_network"
    subnet3s = "172."+str(randSubnet2)+".0"

    labelsall = {
        'neoload-cli': runId
    }

    commonenv = {
        "NEOLOADWEB_URL": user_data.get_user_data().get_url(),
        "NEOLOADWEB_TOKEN": user_data.get_user_data().get_token()
    }

    ctrlenv = {
        "MODE": "Managed",
        "LEASE_SERVER": "NLWEB",
    }
    ctrlenv.update(commonenv)
    ctrlenv["ZONE"] = json['controllerZoneId']

    try:
        network = setup_network(client, networkName, labelsall, subnet3s)

        network_id = network.id

        volumes = {}
        #if isInteractiveMode() and isLoggerInDebug(logger):
        #    volumes[os.getcwd()] = {'bind': '/launch', 'mode': 'ro'}

        lglinks = {}
        baseIpX = 2
        lgs_spec = json['lgZoneIds']
        lg_index = 0
        for zone in lgs_spec:
            numOfLGs = lgs_spec[zone]

            for x in range(numOfLGs):
                creation = setup_lg(client, zone, lg_index, runId, subnet3s, baseIpX, randPortRange, commonenv, lgimage, labelsall, auto_remove_containers, volumes)

                lg = creation['lg']
                lgname = creation['derivedName']
                lghost = creation['hostname']
                lglinks[lg.id] = lgname
                container_ids.append(lg.id)
                lg_container_ids.append(lg.id)
                logging.info("Created load generator " + str(lg_index+1) + ".")

                network.connect(
                    container=lg.id,
                    ipv4_address=lghost
                )
                logging.info("Attached load generator " + str(x+1) + " to network.")

                baseIpX += 1

                lg_index += 1



        ctrl = client.containers.run(
            image=ctrlimage,
            name = key_container_naming_prefix + runId + "_ctrl",
            network = networkName,
            labels = labelsall,
            detach=True,
            auto_remove=auto_remove_containers,
            environment=ctrlenv,
            volumes=volumes,
            #links=lglinks
        )
        container_ids.append(ctrl.id)
        ctrl_container_id = ctrl.id
        logging.info("Attached controller.")

        logging.info("Waiting for docker containers to be attached and ready.")

        waitingSuccess = False

        for container_id in lg_container_ids:
            waitingSuccess = wait_for_logs_to_include(container_id,"Agent started|Connection test to Neoload Web successful|LoadGeneratorAgent running")
            if not waitingSuccess:
                logging.warning("Couldn't ensure load generator readiness for " + container_id)
                break

        if ctrl_container_id is not None:
            waitingSuccess = wait_for_logs_to_include(ctrl_container_id,"Successfully connected to URL")
            if not waitingSuccess:
                logging.warning("Couldn't ensure controller readiness for " + container_id)

        if waitingSuccess:
            logging.info("All containers are attached and ready for use.")

        time.sleep( 5 ) # give a few moments for platform to recognize resources as available

        prior = {
            "runId": runId,
            "tag": tag,
            "ctrlimage": ctrlimage,
            "lgimage": lgimage
        }
        prior[key_spun_at_run] = not explicit
        user_data.set_meta(key_meta_prior_docker, prior)

        isReady = True

    except Exception as err:
        logging.error("Unexpected error in 'attach':")
        traceback.print_exc()



def setup_network(client, networkName, labelsall, subnet3s):
    network = client.networks.create(
        name = networkName,
        driver = "bridge",
        attachable = True,
        labels = labelsall,
        #scope="global",
        ipam = docker.types.IPAMConfig(
            driver = 'default',
            #options={
            #    'subnet': subnet3s+".0/16",
            #    'gateway': subnet3s+".1"
            #}
            pool_configs=[docker.types.IPAMPool(
                subnet = subnet3s+'.0/16',
                iprange = subnet3s+'.0/24',
                gateway = subnet3s+'.254'
            )]
        )
    )
    logging.info("Created docker network '" + networkName + "'")
    logging.debug(network.attrs)
    return network



def setup_lg(client, zone, lg_index, runId, subnet3s, baseIpX, randPortRange, commonenv, lgimage, labelsall, auto_remove_containers, volumes):
    spec = {}

    lgport = randPortRange+lg_index
    lgname = key_container_naming_prefix + runId + "_lg" + str(lg_index+1)
    lghost = subnet3s+"."+str(baseIpX)

    lg2ctrl_port = lgport
    # some Docker environments (like Windows vs. linux/mac) map ports differently
    # apparently on Windows systems, you must map to the dynamic port
    # whereas on linux/Mac, you would route to the default port
    if platform.system().lower() != 'windows':
        lg2ctrl_port = 7100

    hostandport = {
        "LG_HOST": lghost,#"10.0.0.111",#lgname,
        "LG_PORT": lg2ctrl_port,
        "AGENT_SERVER_PORT": lg2ctrl_port
    }
    lgenv = commonenv.copy()
    lgenv.update(hostandport)
    lgenv["ZONE"] = zone

    logging.info("Attaching load generator " + str(lg_index+1) + ".")

    portspec = {}
    portspec[""+str(lgport)+"/tcp"] = lgport
    lg = client.containers.run(
        image=lgimage,
        name = lghost,
        labels = labelsall,
        detach=True,
        auto_remove=auto_remove_containers,
        environment=lgenv,
        volumes=volumes,
        ports=portspec,
    )

    spec['lg'] = lg
    spec['derivedName'] = lgname
    spec['hostname'] = lghost

    return spec



def wait_for_logs_to_include(container_id, str_to_find):
    client = docker.from_env()
    logs = ""
    wait_sec = 0
    started_at = datetime.now()
    strs_to_find = str_to_find.split("|")
    try:
        container = client.containers.get(container_id)
        logging.info("Waiting for container " + container.name + " logs to indicate attachment readiness")

        while wait_sec < max_container_readiness_wait_sec:
            time.sleep(1)
            wait_sec = (datetime.now() - started_at).total_seconds()

            logstr = container.logs()
            if logstr is None: logstr = ""

            for str in strs_to_find:
                if str.lower() in logstr.decode("utf-8").lower():
                    return True

        logging.debug("Timed out while waiting for "+container.name+" readiness.")

    except Exception as err:
        logging.error("Unexpected error in 'wait_for_logs_to_include':", sys.exc_info()[0])
        traceback.print_exc()

    return False



def detach_all_infra(explicit, all):
    client = docker.from_env()

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
            return

    containers = client.containers.list(
        all = True,
        filters = filters,
    )
    networks = client.networks.list(
        filters = filters,
    )
    beforeCount = len(containers) + len(networks)
    if beforeCount < 1:
        logging.info("No containers or networks with 'neoload-cli' label to delete.")
    else:
        logging.info("Containers:\n\t" + "\n\t".join(map(lambda x: x.name, containers)))
        logging.info("Networks:\n\t" + "\n\t".join(map(lambda x: x.name, networks)))

        doIt = 'n'
        if not explicit:
            doIt = 'y'
        elif sys.stdin.isatty():
            doIt = click.prompt("Are you sure you want to delete all containers and networks with the label '" + filters['label'] + "'? (y/n)", 'n', False)

        if doIt == 'y':

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

    afterCount = len(containers) + len(networks)

    logging.info(str(afterCount)+" docker artifacts with label=neoload-cli exist.")

    prior = user_data.get_meta(key_meta_prior_docker)
    if not prior is None:
        prior.pop(key_docker_run_id, None)
        user_data.set_meta(key_meta_prior_docker, prior)

    return beforeCount > 0 and afterCount < 1



def remove_container(client,containerId):
    try:
        container = client.containers.get(containerId)

        #logging.debug("Container " + container.name + " logs:")
        #logging.debug(container.logs().decode("utf-8"))

        logging.info("Stopping container " + containerId)
        container.stop()
        if not auto_remove_containers:
            container.remove()

    except Exception as err:
        if "No such container" in str(sys.exc_info()[0]):
            #logging.info("Tried to remove non-existent container: " + containerId)
            logging.warning("Tried to remove non-existent container: " + containerId)
        else:
            #logging.error("Unexpected error in 'remove_container':", sys.exc_info()[0])
            traceback.print_exc()



def remove_network(client,networkId):
    logging.info("Removing network " + networkId)
    try:
        network = client.networks.get(networkId)
        network.remove()
    except Exception as err:
        #logging.error("Unexpected error in 'remove_network':", sys.exc_info()[0])
        traceback.print_exc()
