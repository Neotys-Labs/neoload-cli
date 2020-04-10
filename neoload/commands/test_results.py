import click
import sys
import json

from neoload_cli_lib import tools, rest_crud, user_data, displayer
from neoload_cli_lib.name_resolver import Resolver

__endpoint = "v2/test-results"
__operation_statistics = "/statistics"
__operation_sla_global = "/slas/statistics"
__operation_sla_test = "/slas/per-test"
__operation_sla_interval = "/slas/per-interval"

__resolver = Resolver(__endpoint)

meta_key = 'result id'


@click.command()
@click.argument('command', type=click.Choice(['ls', 'summary', 'patch', 'delete', 'use'], case_sensitive=False),
                required=False)
@click.argument("name", type=str, required=False)
@click.option('--rename', help="")
@click.option('--description', help="")
@click.option('--quality-status', 'quality_status', type=click.Choice(['PASSED', 'FAILED']), help="")
@click.option('--junit-file', 'junit_file', default="junit-sla.xml", help="Output the junit sla report to this path")
def cli(command, name, rename, description, quality_status, junit_file):
    """create/read/update/delete test settings"""
    if not command:
        print("command is mandatory. Please see neoload tests-settings --help")
        return
    rest_crud.set_current_sub_command(command)
    if name == "cur":
        name = user_data.get_meta(meta_key)
    is_id = tools.is_id(name)
    # avoid to make two requests if we have not id.
    if command == "ls":
        tools.ls(name, is_id, __resolver)
        return

    __id = get_id(name, is_id)

    if command == "use":
        tools.use(__id, meta_key, __resolver)
        return

    if not __id:
        __id = user_data.get_meta(meta_key)

    if command == "summary":
        json_result = rest_crud.get(get_end_point(__id))
        json_sla_global = rest_crud.get(get_end_point(__id, __operation_sla_global))
        json_sla_test = rest_crud.get(get_end_point(__id, __operation_sla_test))
        json_sla_interval = rest_crud.get(get_end_point(__id, __operation_sla_interval))
        json_stats = rest_crud.get(get_end_point(__id, __operation_statistics))
        displayer.print_result_summary(json_result, json_sla_global, json_sla_test, json_sla_interval, json_stats)
        user_data.set_meta(meta_key, __id)
    if command == "junitsla":
        json_result = rest_crud.get(get_end_point(__id))
        json_sla_test = rest_crud.get(get_end_point(__id, __operation_sla_test))
        json_sla_interval = rest_crud.get(get_end_point(__id, __operation_sla_interval))
        displayer.print_result_junit(json_result, json_sla_test, json_sla_interval, junit_file)
        user_data.set_meta(meta_key, __id)
    elif command == "patch":
        json_data = create_json(rename, description, quality_status)
        rep = rest_crud.put(get_end_point(__id), json_data)
        tools.get_id_and_print_json(rep)
        user_data.set_meta(meta_key, __id)
    elif command == "delete":
        rep = tools.delete(__endpoint, __id, "test results")
        tools.print_json(rep.json())
        if rep['code'] != '204':
            raise click.ClickException('Operation may have failed !')
        user_data.set_meta(meta_key, None)


def get_id(name, is_id):
    if is_id or not name:
        return name
    else:
        return __resolver.resolve_name(name)


def get_end_point(id_test: str, operation=''):
    return __endpoint + "/" + id_test + operation


def create_json(name, description, quality_status):
    data = {}
    if name is not None:
        data['name'] = name
    if description is not None:
        data['description'] = description
    if quality_status is not None:
        data['qualityStatus'] = quality_status

    if len(data) == 0:
        if sys.stdin.isatty():
            for field in ['name', 'description', 'qualityStatus']:
                data[field] = input(field)
        else:
            try:
                return json.loads(sys.stdin.read())
            except json.JSONDecodeError as err:
                raise click.ClickException('%s\nThis command requires a valid Json input.\n'
                                           'Example: neoload test-results put {"name":"TestResultName"}' % str(err))
    return data
