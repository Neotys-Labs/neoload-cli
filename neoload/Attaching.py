
from neoload import *

import os
import sys
import traceback
import docker
import random
import time
import logging
import platform
from datetime import datetime
import pprint

auto_remove_containers = True
max_container_readiness_wait_sec = 60

def attachInfra(profile,rawspec):
    spec = parseInfraSpec(rawspec)
    if spec["provider"] == "docker":
        return attachLocalDockerInfra(profile,spec)
    else:
        raise NotImplementedError()

def detatchInfra(spec):
    logger = logging.getLogger("root")
    logger.info("detatchInfra: "+spec["provider"])
    if spec["provider"] == "docker":
        return detatchLocalDockerInfra(spec)
    else:
        logger.info("Attached infrastructure lacked a provider, so no detatched occured.")

_containerNamingPrefix = "neoload_cli"

def attachLocalDockerInfra(profile,spec):
    logger = logging.getLogger("root")

    logger.warning("Connecting to local Docker host")
    client = docker.from_env()

    use_nts = "ntsurl" in profile and "ntslogin" in profile

    commonenv = {
        "NEOLOADWEB_URL": profile["url"],
        "NEOLOADWEB_TOKEN": profile["token"],
        "ZONE": profile["zone"],
    }
    ctrlenv = {
        "MODE": "Managed",
        "LEASE_SERVER": "NTS" if use_nts else "NLWEB",
    }
    ctrlenv.update(commonenv)
    if use_nts:
        nts = {
            "NTS_URL": profile["ntsurl"],
            "NTS_LOGIN": profile["ntslogin"],
        }
        ctrlenv.update(nts)
    else:
        logger.warning("Because there is no NTS configuration in this profile, license will be acquired from NLWEB.")

    container_ids = []
    lg_container_ids = []
    ctrl_container_id = None
    network_id = None
    runId = str(random.randint(1,65535))
    randPortRange = random.randint(171,471)*100 # between 17100 and 47100
    #randPortRange = 7100
    randSubnet2 = random.randint(50,250)
    networkName = _containerNamingPrefix + runId + "_network"
    subnet3s = "172."+str(randSubnet2)+".0"
    try:
        network = client.networks.create(
            networkName,
            driver="bridge",
            attachable=True,
            #scope="global",
            ipam=docker.types.IPAMConfig(
                driver='default',
                #options={
                #    'subnet': subnet3s+".0/16",
                #    'gateway': subnet3s+".1"
                #}
                pool_configs=[docker.types.IPAMPool(
                    subnet=subnet3s+'.0/16',
                    iprange=subnet3s+'.0/24',
                    gateway=subnet3s+'.254'
                )]
            )
        )
        logger.info("Created docker network '" + networkName + "'")
        logger.debug(network.attrs)
        spec["network_id"] = network.id

        volumes = {}
        if isInteractiveMode() and isLoggerInDebug(logger):
            volumes[os.getcwd()] = {'bind': '/launch', 'mode': 'ro'}

        lglinks = {}
        lgImage = spec["lgImage"]
        lgTag = lgImage.split(':')[-1].split("-")[0]
        lgVersion = "" if not lgTag.replace(".","").isnumeric() else lgTag
        logger.debug("lgTag: " + lgTag)
        logger.debug("lgVersion: " + lgVersion)
        baseIpX = 2
        for x in range(spec["numOfLGs"]):
            lgport = randPortRange+x
            lgname = _containerNamingPrefix + runId + "_lg" + str(x+1)
            lghost = subnet3s+"."+str(baseIpX)

            lg2ctrl_port = lgport
            if lgVersion.startswith('7.'):
                lg2ctrl_port = 7100

            hostandport = {
                "LG_HOST": lghost,#"10.0.0.111",#lgname,
                "LG_PORT": lg2ctrl_port
            }
            lgenv = commonenv.copy()
            lgenv.update(hostandport)
            logger.info("Attaching load generator " + str(x+1) + ".")
            portspec = {}
            portspec[""+str(lgport)+"/tcp"] = lgport
            lg = client.containers.run(
                image=lgImage,
                name = lghost,#lgname,
                #network = networkName,
                detach=True,
                auto_remove=auto_remove_containers,
                environment=lgenv,
                volumes=volumes,
                ports=portspec,
            )
            lglinks[lg.id] = lgname
            container_ids.append(lg.id)
            lg_container_ids.append(lg.id)
            logger.info("Created load generator " + str(x+1) + ".")

            network.connect(
                container=lg.id,
                ipv4_address=lghost
            )
            logger.info("Attached load generator " + str(x+1) + " to network.")

            baseIpX += 1

        ctrl = client.containers.run(
            image=spec["ctrlImage"],
            name = _containerNamingPrefix + runId + "_ctrl",
            network = networkName,
            detach=True,
            auto_remove=auto_remove_containers,
            environment=ctrlenv,
            volumes=volumes,
            #links=lglinks
        )
        container_ids.append(ctrl.id)
        ctrl_container_id = ctrl.id
        logger.info("Attached controller.")

        logger.info("Waiting for docker containers to be attached and ready.")

        #neoload.agent.Agent: Connection test to Neoload Web successful
        #neoload.controller.agent.ControllerAgent: Successfully connected to URL:

        waitingSuccess = False

        for container_id in lg_container_ids:
            waitingSuccess = waitForContainerLogsToInclude(container_id,"Agent started|Connection test to Neoload Web successful|LoadGeneratorAgent running")
            if not waitingSuccess:
                logger.error("Couldn't ensure load generator readiness for " + container_id)
                break

        if ctrl_container_id is not None:
            waitingSuccess = waitForContainerLogsToInclude(ctrl_container_id,"Successfully connected to URL")
            if not waitingSuccess:
                logger.error("Couldn't ensure controller readiness for " + container_id)

        if waitingSuccess:
            logger.info("All containers are attached and ready for use.")

        if not pauseIfInteractiveDebug(logger):
            time.sleep( 1 )

        spec["ready"] = True
    except Exception as err:
        logger.error("Unexpected error in 'attachLocalDockerInfra':", sys.exc_info()[0])
        traceback.print_exc()
        spec["ready"] = False

    spec["container_ids"] = container_ids

    return spec

def waitForContainerLogsToInclude(container_id, str_to_find):
    logger = logging.getLogger("root")
    logger.info("Waiting for container " + container_id + " logs to indicate attachment readiness")
    client = docker.from_env()
    logs = ""
    wait_sec = 0
    started_at = datetime.now()
    strs_to_find = str_to_find.split("|")
    try:
        container = client.containers.get(container_id)

        while wait_sec < max_container_readiness_wait_sec:
            time.sleep(1)
            wait_sec = (datetime.now() - started_at).total_seconds()

            logstr = container.logs()
            if logstr is None: logstr = ""

            for str in strs_to_find:
                if str.lower() in logstr.decode("utf-8").lower():
                    logger.debug("Waited successfully for container "+container_id+" readiness.")
                    return True

        logger.debug("Timed out while waiting for "+container_id+" readiness.")

    except Exception as err:
        logger.error("Unexpected error in 'waitForContainerLogsToInclude':", sys.exc_info()[0])
        traceback.print_exc()

    return False


def detatchLocalDockerInfra(spec):
    logger = logging.getLogger("root")
    client = docker.from_env()
    logger.debug(spec)

    pauseIfInteractiveDebug(logger,"Press any key to continue detatching Docker resources...")

    if 'container_ids' in spec:
        for id in spec["container_ids"]:
            try:
                container = client.containers.get(id)

                logger.debug("Container " + container.name + " logs:")
                logger.debug(container.logs())

                logger.info("Stopping container " + id)
                container.stop()
                if not auto_remove_containers:
                    container.remove()

            except Exception as err:
                logger.error("Unexpected error in 'detatchLocalDockerInfra'[0]:", sys.exc_info()[0])
                traceback.print_exc()

    time.sleep( 5 )

    if 'network_id' in spec:
        networkId = spec["network_id"]
        if networkId is not None:
            logger.info("Removing network " + networkId)
            try:
                network = client.networks.get(networkId)
                network.remove()
            except Exception as err:
                logger.error("Unexpected error in 'detatchLocalDockerInfra'[1]:", sys.exc_info()[0])
                traceback.print_exc()

def parseInfraSpec(rawspec):
    # docker#2,neotys/neoload-loadgenerator:6.10
    ret = {
        "ready": False,
        "provider": None,
    }
    parts = rawspec.split("#")
    provider = parts[0].lower()

    ret["provider"] = provider

    if provider == "docker":
        numOfLGs = 1
        lgImage = "neotys/neoload-loadgenerator:latest"
        if len(parts)>1:
            lgparts = parts[1].split(",")
            if lgparts[0].isdigit():
                numOfLGs = int(lgparts[0])
            else:
                raise ValueError("Unknown docker spec for load generators.")

            if len(lgparts)>1:
                lgImage = lgparts[1]

        if numOfLGs > 10:
            raise ValueError("Don't let's be silly. You cannot have more than 10 load generator containers on the same host.")

        ret["numOfLGs"] = numOfLGs
        ret["ctrlImage"] = lgImage.replace("-loadgenerator","-controller")
        ret["lgImage"] = lgImage
        return ret
    else:
        raise ValueError("Unknown provider prefix in infrastructure specification.")
