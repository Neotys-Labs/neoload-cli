import traceback

import click

_CliException__debug = False


def set_debug(boolean: bool):
    global _CliException__debug
    _CliException__debug = boolean


class CliException(click.ClickException):
    def __init__(self, message):
        super().__init__(message)

    def format_message(self):
        global __debug
        __message = super().format_message()
        if __debug:
            __message = traceback.format_exc() + "\n\n" + __message
        return __message
