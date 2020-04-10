import datetime
import json
import time
from signal import signal, SIGINT

from commands import logs_url,test_results
from neoload_cli_lib import tools, rest_crud

__current_id = None
__endpoint = "v2/tests-results/"
__count = 0

__last_status = ""


def handler(signal_received, frame):
    global __count
    if __current_id:
        inc = stop(__current_id, __count > 0, True)
        if inc:
            __count += 1


def wait(results_id):
    global __current_id
    __current_id = results_id
    signal(SIGINT, handler)
    header_status(results_id)
    while display_status(results_id):
        time.sleep(5)

    __current_id = None
    test_results.summary(results_id)


def header_status(results_id):
    print("Results of  : " + results_id)
    print("Logs are available at " + logs_url.get_url(results_id))


# INIT, STARTING, RUNNING, TERMINATED
def display_status(results_id):
    global __last_status
    res = rest_crud.get('v2/test_result' + results_id)
    status = res['status']

    if __last_status != status:
        print("Status: " + status)
        __last_status = status
    if status == "RUNNING":
        display_statistics(results_id, res)

    return True


def display_statistics(results_id, json_summary):
    res = rest_crud.get('v2/test_result/' + results_id + '/statistics')
    time_cur = datetime.datetime.now() - datetime.datetime.utcfromtimestamp((json_summary['startDate']))
    time_cur_format = datetime.datetime.strptime(time_cur, '%Y-%m-%d %H:%M:%S.%f')
    lg_count = json_summary['lgCount']
    duration_raw = json_summary['duration']
    duration = duration_raw if duration_raw else " - "
    throutput = res['totalGlobalDownloadedBytesPerSecond']
    error_count = res['totalGlobalCountFailure']
    vu_count = res['lastVirtualUserCount']
    request_sec = res['lastRequestCountPerSecond']
    request_duration = res['totalRequestDurationAverage']
    print(
        f'    {time_cur_format}/{duration}\t Err[{error_count}], LGs[{lg_count}]\t VUs:{vu_count}\t BPS[{throutput}]\t RPS:{request_sec}\t avg(rql): {request_duration}')


def stop(results_id, force: bool, quit_option=False):
    policy = 'FORCE' if force else 'GRACEFUL'
    map_policy = {"stopPolicy": policy}
    if tools.confirm("Do you want stop the test" + results_id + " with " + policy.lower() + " policy ?", quit_option):
        rest_crud.post(__endpoint + "/" + results_id + "/stop", json.dumps(map_policy))
        return True
    return False
