import traceback

import click

_CliException__debug = False


class CliException(click.ClickException):
    __debug = False

    @staticmethod
    def set_debug(boolean: bool):
        CliException.__debug = boolean

    def __init__(self, message):
        super().__init__(message)

    def format_message(self):
        __message = super().format_message()
        if CliException.__debug:
            __message = traceback.format_exc() + "\n\n" + __message
        return __message
