import click

from commands import test_settings, test_results
from neoload_cli_lib import user_data, tools, displayer, running_tools
from neoload_cli_lib import tools
import logging
import yaml
from datetime import datetime, date
import time
import sys
import traceback

@click.command()
@click.argument('command', type=click.Choice(['slas'], case_sensitive=False))
@click.argument("name", type=str, required=False)
@click.option("--stop", 'stop', is_flag=True, default=True, help="Doesn't wait the end of test")
@click.option("--force", 'force', is_flag=True, default=True, help="Doesn't wait the end of test")
@click.option("--max-failure", 'max_failure', type=int, default=0, help="Max SLA failure threshold; default is zero")
def cli(command, name, stop, force, max_failure): #, max_occurs):
    """Fails if certain conditions are met, such as per-run SLAs failed % of time"""
    if not command:
        tools.system_exit({'message': "command is mandatory. Please see neoload fastfail --help", 'code': 2})
        return

    if max_failure < 0 or max_failure > 100:
        tools.system_exit({'message': "--max-failure percentage tolerance must be between 0 and 100", 'code': 2})
        return


    if command == "slas":
        monitor_loop(name, stop, force, max_failure)

    else:
        tools.system_exit({'message': "Invalid command. Please see neoload fastfail --help", 'code': 2})

def monitor_loop(name, stop, force, max_failure):
    dt_started = datetime.now()
    print('fastfail started: ' + str(dt_started))
    dt_current = dt_started

    if sys.stdin.isatty():
        sys.stdout = Unbuffered(sys.stdout)

    is_initializing = False
    is_running = False
    has_exited = False
    while (abs(dt_current-dt_started).seconds / 60) < 10:
        datas = test_results.get_sla_data_by_name_or_id(name)

        partial_intervals = list(filter(lambda x: x['status']=='FAILED',datas['sla_interval']))
        failed_intervals = list(filter(lambda x: x['failed']>=max_failure,partial_intervals))

        fails = []
        fails.extend(list(filter(lambda x: x['status']=='FAILED',datas['sla_global'])))
        fails.extend(list(filter(lambda x: x['status']=='FAILED',datas['sla_test'])))
        fails.extend(failed_intervals)

        status = datas['result']['status']
        quality_status = datas['result']['qualityStatus']

        msg = "{0} hard SLA failures, test status {1},{2}".format(len(fails), status, quality_status)
        if len(partial_intervals) > 0 and len(failed_intervals) < 1:
            msg += "\nSome SLAs failed, but were not above max-failure of {0}% so did not count as error.".format(max_failure)

        outcomes = process_state(datas,fails,stop,force,is_initializing,is_running,msg)

        final_run = has_exited and outcomes["has_exited"]
        has_exited = outcomes["has_exited"]
        is_initializing = outcomes["is_initializing"]
        is_running = outcomes["is_running"]

        if not final_run and len(fails) > 0 or len(partial_intervals) > 0:
            displayer.__print_sla(datas['sla_global'], datas['sla_test'], datas['sla_interval'])

        if final_run:
            break

        printif(sys.stdin.isatty() and not has_exited, '.', end = '')

        time.sleep(5)

        dt_current = datetime.now()

    print('fastfail ended: ' + str(dt_current))

def process_state(datas,fails,stop,force,is_initializing,is_running,msg):
    ret = {
        "has_exited": False,
        "is_initializing": is_initializing,
        "is_running": is_running
    }
    status = datas['result']['status']

    if len(fails) > 0:
        if status != 'TERMINATED':
            if stop:
                print("\nStopping test, force={0}".format(force))
                tools.set_batch(True)
                running_tools.stop(datas["id"], force)
        else:
            tools.system_exit({'message': msg, 'code': 1})
        ret["has_exited"] = True
    elif status == 'TERMINATED':
        tools.system_exit({'message': msg, 'code': 0 if datas['result']['qualityStatus']=="PASSED" else 1})
        ret["has_exited"] = True
    elif status == 'INIT':
        printif(not is_initializing, 'Initializing', end = '')
        is_initializing = True
    elif status == 'RUNNING':
        printif(not is_running, '\nRunning', end = '')
        is_running = True

    ret["is_initializing"] = is_initializing
    ret["is_running"] = is_running

    return ret

def printif(should_print, msg, end='\n'):
    if should_print:
        print(msg,end=end)

class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
   def write(self, data):
       self.stream.write(data)
       self.stream.flush()
   def writelines(self, datas):
       self.stream.writelines(datas)
       self.stream.flush()
   def __getattr__(self, attr):
       return getattr(self.stream, attr)
