import sys
import click
import docker

from neoload_cli_lib import user_data

_containerNamingPrefix = "neoload_cli"

@click.command()
@click.argument("command", required=True, type=click.Choice(['ls', 'attach', 'detach', 'forget']))
@click.option('--tag', default="latest", help="The docker image version to use")
@click.option('--ctrlimage', default="neotys/neoload-controller", help="The controller image to use")
@click.option('--lgimage', default="neotys/neoload-loadgenerator", help="The load generator image to use")
def cli(command, tag, ctrlimage, lgimage):

    if command == "attach":
        attach(tag, ctrlimage, lgimage)
    else:
        raise ValueError("Command '" + command + "' not yet implemented.")


def attach(tag, ctrlimage, lgimage):

    client = docker.from_env()

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
    labelsall = {
        'neoload-cli': runId
    }

    try:
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
        #cprintOrLogInfo(explicit,logger,"Created docker network '" + networkName + "'")
        #logger.debug(network.attrs)
        spec["network_id"] = network.id

        volumes = {}
        #if isInteractiveMode() and isLoggerInDebug(logger):
        #    volumes[os.getcwd()] = {'bind': '/launch', 'mode': 'ro'}

        lglinks = {}
        baseIpX = 2
        for x in range(spec["numOfLGs"]):
            lgport = randPortRange+x
            lgname = _containerNamingPrefix + runId + "_lg" + str(x+1)
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
            cprintOrLogInfo(explicit,logger,"Attaching load generator " + str(x+1) + ".")
            portspec = {}
            portspec[""+str(lgport)+"/tcp"] = lgport
            lg = client.containers.run(
                image=lgimage,
                name = lghost,#lgname,
                #network = networkName, # handled with explicit .connect below
                labels = labelsall,
                detach=True,
                auto_remove=auto_remove_containers,
                environment=lgenv,
                volumes=volumes,
                ports=portspec,
            )
            lglinks[lg.id] = lgname
            container_ids.append(lg.id)
            lg_container_ids.append(lg.id)
            cprint("Created load generator " + str(x+1) + ".")

            network.connect(
                container=lg.id,
                ipv4_address=lghost
            )
            cprint("Attached load generator " + str(x+1) + " to network.")

            baseIpX += 1

        ctrl = client.containers.run(
            image=ctrlimage,
            name = _containerNamingPrefix + runId + "_ctrl",
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
        print("Attached controller.")

        print("Waiting for docker containers to be attached and ready.")

        #neoload.agent.Agent: Connection test to Neoload Web successful
        #neoload.controller.agent.ControllerAgent: Successfully connected to URL:

        waitingSuccess = False

        for container_id in lg_container_ids:
            waitingSuccess = waitForContainerLogsToInclude(explicit,logger,container_id,"Agent started|Connection test to Neoload Web successful|LoadGeneratorAgent running")
            if not waitingSuccess:
                print("Couldn't ensure load generator readiness for " + container_id)
                break

        if ctrl_container_id is not None:
            waitingSuccess = waitForContainerLogsToInclude(explicit,logger,ctrl_container_id,"Successfully connected to URL")
            if not waitingSuccess:
                print("Couldn't ensure controller readiness for " + container_id)

        if waitingSuccess:
            print("All containers are attached and ready for use.")

        #if not pauseIfInteractiveDebug(logger):
        #    time.sleep( 5 )

        spec["ready"] = True

    except Exception as err:
        print("Unexpected error in 'attachLocalDockerInfra':")
        traceback.print_exc()
        spec["ready"] = False
