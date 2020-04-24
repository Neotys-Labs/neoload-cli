import datetime
import time
from signal import signal, SIGINT

from commands import logs_url, test_results, docker
from neoload_cli_lib import tools, rest_crud

import sys
import webbrowser

__current_id = None
__endpoint = "v2/test-results/"
__count = 0

__last_status = ""


def handler(signal_received, frame):
    global __count
    if __current_id:
        inc = stop(__current_id, __count > 0, True)
        if inc:
            __count += 1


def wait(results_id, exit_code_sla):
    global __current_id
    __current_id = results_id
    signal(SIGINT, handler)
    header_status(results_id)
    time.sleep(5)
    while display_status(results_id):
        time.sleep(20)

    __current_id = None
    docker.cleanup_after_test()
    tools.system_exit(test_results.summary(results_id), exit_code_sla)


def header_status(results_id):
    url = logs_url.get_url(results_id)
    print("Results of  : " + results_id)
    print("Logs are available at " + url)
    if sys.stdin.isatty():
        time.sleep( 1 )
        webbrowser.open_new_tab(url)


# INIT, STARTING, RUNNING, TERMINATED
def display_status(results_id):
    global __last_status
    res = rest_crud.get('v2/test-results/' + results_id)
    status = res['status']

    if __last_status != status:
        print("Status: " + status)
        __last_status = status
    if status == "RUNNING":
        display_statistics(results_id, res)
    if status == "TERMINATED":
        return False

    return True


def display_statistics(results_id, json_summary):
    res = rest_crud.get(__endpoint + results_id + '/statistics')
    time_cur = datetime.datetime.now() - datetime.datetime.fromtimestamp((json_summary['startDate'] + 1) / 1000)
    time_cur_format = format_delta(time_cur)
    lg_count = json_summary['lgCount']
    duration_raw = json_summary['duration']
    duration = format_delta(datetime.timedelta(seconds=(duration_raw / 1000))) if duration_raw else " - "
    throughput = res['totalGlobalDownloadedBytesPerSecond']
    error_count = res['totalGlobalCountFailure']
    vu_count = res['lastVirtualUserCount']
    request_sec = res['lastRequestCountPerSecond']
    request_duration = res['totalRequestDurationAverage']
    print(
        f'    {time_cur_format}/{duration}\t Err[{error_count}], LGs[{lg_count}]\t VUs:{vu_count}\t BPS[{throughput}]\t RPS:{request_sec:.3f}\t avg(rql): {request_duration}')


def format_delta(delta):
    hour, remaining_sec = divmod(delta.seconds, 3600)
    minute, sec = divmod(remaining_sec, 60)
    return f'{delta.days + "d" if delta.days > 0 else ""}{hour:02d}:{minute:02d}:{sec:02d}'


def stop(results_id, force: bool, quit_option=False):
    policy = 'TERMINATE' if force else 'GRACEFUL'
    if tools.confirm("Do you want stop the test" + results_id + " with " + policy.lower() + " policy ?", quit_option):
        rest_crud.post(__endpoint + results_id + "/stop", {"stopPolicy": policy})
        docker.cleanup_after_test()
        return True
    return False
