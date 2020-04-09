import json
from signal import signal, SIGINT

from neoload_cli_lib import tools, rest_crud
from commands import test_results


def handler(signal_received, frame):
    # Handle any cleanup here
    print('SIGINT or CTRL-C detected. Exiting gracefully')


def wait(results_id):
    signal(SIGINT, handler)

    pass


__endpoint = "v2/tests-results/"


def stop(results_id, force: bool):
    policy = 'FORCE' if force else 'GRACEFUL'
    map_policy = {"stopPolicy": policy}
    if tools.confirm("Do you want stop the test" + results_id + " with " + policy.lower() + " policy ?"):
        rest_crud.post(__endpoint + "/" + results_id + "/stop", json.dumps(map_policy))
