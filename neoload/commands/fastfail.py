import click

from commands import test_settings, test_results
from neoload_cli_lib import user_data, tools, displayer, running_tools
from neoload_cli_lib.tools import upgrade_logging,downgrade_logging
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
        print("command is mandatory. Please see neoload fastfail --help")
        return

    if max_failure < 0 or max_failure > 100:
        print("--max-failure percentage tolerance must be between 0 and 100")
        return


    if command == "slas":
        monitor_loop(name, stop, force, max_failure)
        return

    else:
        print("Invalid command. Please see neoload fastfail --help")
        return

def monitor_loop(name, stop, force, max_failure):
    dt_started = datetime.now()
    dt_current = dt_started

    if sys.stdin.isatty():
        sys.stdout = Unbuffered(sys.stdout)
        
    is_initializing = False
    is_running = False
    while (abs(dt_current-dt_started).seconds / 60) < 10:
        datas = test_results.get_sla_data_by_name_or_id(name)

        partial_intervals = list(filter(lambda x: x['status']=='FAILED',datas['sla_interval']))
        failed_intervals = list(filter(lambda x: x['failed']>=max_failure,partial_intervals))

        fails = []
        fails.extend(list(filter(lambda x: x['status']=='FAILED',datas['sla_global'])))
        fails.extend(list(filter(lambda x: x['status']=='FAILED',datas['sla_test'])))
        fails.extend(failed_intervals)

        if len(fails) > 0 or len(partial_intervals) > 0:
            print('\n\n')
            displayer.__print_sla(datas['sla_global'], datas['sla_test'], datas['sla_interval'])
            #print(yaml.dump(fails))

        status = datas['result']['status']
        qualityStatus = datas['result']['qualityStatus']

        msg = "{0} hard SLA failures, test status {1},{2}".format(len(fails), status, qualityStatus)
        if len(partial_intervals) > 0 and len(failed_intervals) < 1:
            msg += "\nSome SLAs failed, but were not above max-failure of {0}% so did not count as error.".format(max_failure)


        if len(fails) > 0:
            if stop and status != 'TERMINATED':
                print("Stopping test, force={0}".format(force))
                tools.set_batch(True)
                running_tools.stop(datas['id'], force)
            tools.system_exit({'message': msg, 'code': 1})
            break
        elif status == 'TERMINATED':
            tools.system_exit({'message': msg, 'code': 0})
            break
        elif status == 'INIT':
            if not is_initializing:
                print('Initializing', end = '')
            is_initializing = True
        elif status == 'RUNNING':
            if not is_running:
                print('Running', end = '')
            is_running = True

        print('.', end = '')
        time.sleep(5)

        dt_current = datetime.now()

def get_id(name, is_id):
    if is_id or not name:
        return name
    else:
        return __resolver.resolve_name(name)

def get_end_point(id_test: str, operation=''):
    return __endpoint + "/" + id_test + operation

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
