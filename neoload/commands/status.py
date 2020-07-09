import click

from commands import test_settings, test_results
from neoload_cli_lib import user_data
from neoload_cli_lib.tools import upgrade_logging,downgrade_logging
import logging
from urllib3.exceptions import ConnectTimeoutError
from requests.exceptions import ConnectTimeout
import sys
import traceback

@click.command()
def cli():
    """get status of NeoLoad cli Settings"""
    login = user_data.get_user_data(False)
    if login is None:
        print("No settings is stored. Please use \"neoload login\" to start.")
    else:
        print(augment_with_names(login))
    pass

def augment_with_names(data):
    output = str(data)

    try:
        if test_settings.is_current_test_settings_set():
            json = test_settings.get_current_test_settings_json()
            settings_id = data.metadata[test_settings.meta_key]
            output = output.replace(settings_id,settings_id + " ({name})".format(**json))

        if test_results.is_current_test_results_set():
            json = test_results.get_current_test_results_json()
            results_id = data.metadata[test_results.meta_key]
            output = output.replace(results_id,results_id + " ({project}|{scenario}|{name}) {status}|{qualityStatus}".format(**json))
    except (ConnectTimeoutError,ConnectTimeout):
        logging.warning('Connection to current NeoLoad Web server failed while collecting current test metadata.')
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        full_msg = repr(traceback.format_exception(exc_type, exc_value,
                                          exc_traceback))
        upgrade_logging()
        logging.warning('Could not obtain test and/or result metadata: ' + full_msg)
        downgrade_logging()

    return output
