import datetime
import logging
import time
import webbrowser
from signal import signal, SIGINT

from commands import logs_url, test_results
from commands import run
from neoload_cli_lib import tools, rest_crud,hooks

__current_id = None
__count = 0

__last_status = ""

def __is_current_state_running(status):
    return status == "RUNNING"

def __is_current_state_terminated_and_not_unknown(status, quality_status):
    # this mehtod represent when a test is terminated but not aborted
    # this specific state is when the test is 'TERMINATED' but quality status is not 'UNKNOWN'
    return status == "TERMINATED" and quality_status != "UNKNOWN"

def __lock_result(results_id, data_lock):
    run.patch_data(results_id, data_lock)
    data_lock.clear() # after patch you never "patch lock" while running, so data_lock is delete to skip "patch lock" of the loop in display_status

def handler(signal_received, frame):
    global __count
    logging.debug("Ctrl+C is pressed or SIGINT is handled")
    if __current_id:
        inc = stop(__current_id, __count > 0, True)
        if inc:
            __count += 1


def wait(results_id, exit_code_sla, data_lock): # data_lock is needed to lock result when test state is running
    global __current_id
    __current_id = results_id
    signal(SIGINT, handler)
    header_status(results_id)
    while display_status(results_id, data_lock):
        time.sleep(20)

    __current_id = None
    hooks.trig("test.stop")
    tools.system_exit(test_results.summary(results_id), exit_code_sla)


def header_status(results_id):
    url = logs_url.get_url(results_id)
    print("Results of  : " + results_id)
    print("Logs are available at " + url)
    if tools.is_user_interactive():
        time.sleep(1)
        webbrowser.open_new_tab(url)

# INIT, STARTING, RUNNING, TERMINATED
def display_status(results_id, data_lock): 
    global __last_status
    res = rest_crud.get(test_results.get_end_point(results_id))
    status = res.get('status')
    quality_status = res.get('qualityStatus')

    if __last_status != status:
        print("Status: " + status)
        __last_status = status
    if data_lock != {}: #if there is data in data_lock we know that we want to lock our test result
        if __is_current_state_running(status):
            __lock_result(results_id, data_lock)
        if __is_current_state_terminated_and_not_unknown(status, quality_status):
            __lock_result(results_id, data_lock)
    if status == "RUNNING":
        display_statistics(results_id, res)
    if status == "TERMINATED":
        return False

    return True


def display_statistics(results_id, json_summary):
    res = rest_crud.get(test_results.get_end_point(results_id, '/statistics'))
    time_cur = datetime.datetime.now() - datetime.datetime.fromtimestamp((json_summary['startDate'] + 1) / 1000)
    time_cur_format = format_delta(time_cur)
    lg_count = json_summary.get('lgCount') or '--'
    duration_raw = json_summary.get('duration')
    duration = format_delta(datetime.timedelta(seconds=(duration_raw / 1000))) if duration_raw else " - "
    throughput = res.get('totalGlobalDownloadedBytesPerSecond') or '--'
    error_count = res.get('totalGlobalCountFailure') or '--'
    vu_count = res.get('lastVirtualUserCount') or '--'
    request_sec_raw = res.get('lastRequestCountPerSecond')
    request_sec = f'{request_sec_raw:.3f}' if request_sec_raw else '--'
    request_duration = res.get('totalRequestDurationAverage') or '--'
    print(
        f'    {time_cur_format}/{duration}\t Err[{error_count}], LGs[{lg_count}]\t VUs:{vu_count}\t BPS[{throughput}]\t RPS:{request_sec}\t avg(rql): {request_duration}')


def format_delta(delta):
    hour, remaining_sec = divmod(delta.seconds, 3600)
    minute, sec = divmod(remaining_sec, 60)
    return f'{str(delta.days) + "d" if delta.days > 0 else ""}{hour:02d}:{minute:02d}:{sec:02d}'


def stop(results_id, force: bool, quit_option=False):
    policy = 'TERMINATE' if force else 'GRACEFUL'
    if tools.confirm("Do you want stop the test" + results_id + " with " + policy.lower() + " policy ?", quit_option):
        rest_crud.post(test_results.get_end_point(results_id, "/stop"), {"stopPolicy": policy})
        hooks.trig("test.stop")
        return True
    return False