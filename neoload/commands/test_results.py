import json
import sys

import click

from neoload_cli_lib import tools, rest_crud, user_data, displayer, cli_exception
from neoload_cli_lib.name_resolver import Resolver

__endpoint = "/test-results"
__operation_statistics = "/statistics"
__operation_sla_global = "/slas/statistics"
__operation_sla_test = "/slas/per-test"
__operation_sla_interval = "/slas/per-interval"

__resolver = Resolver(__endpoint, rest_crud.base_endpoint_with_workspace)

meta_key = 'result id'

def load_from_file(file):
    try:
        return json.load(file)
    except json.JSONDecodeError as err:
        raise cli_exception.CliException('%s\nThis command requires a valid Json input.\n'
                                         'Example: neoload test-settings create {"name":"TestName"}' % str(err))

@click.command()
@click.argument('command',
                type=click.Choice(['ls', 'summary', 'junitsla', 'put', 'patch', 'delete', 'use'], case_sensitive=False),
                required=False)
@click.argument("name", type=str, required=False)
@click.option('--rename', help="")
@click.option('--description', help="")
@click.option('--quality-status', 'quality_status', type=click.Choice(['PASSED', 'FAILED']), help="")
@click.option('--junit-file', 'junit_file', default="junit-sla.xml", help="Output the junit sla report to this path")
@click.option('--file', type=click.File('r'), help="Json file with the data to be sent to the API.")
def cli(command, name, rename, description, quality_status, junit_file, file):
    """
    ls       # Lists test results                                            .
    summary  # Display a summary of the result : SLAs and statistics         .
    junitsla # Output SLA results to a file with junit format                .
    put      # Update the name, description or quality-status of the result  .
    delete   # Remove a result                                               .
    use      # Remember the test result you want to work on. Example : neoload
    |          test-results use MyTest#1 ; neoload test-results summary      .
    """
    if not command:
        print("command is mandatory. Please see neoload tests-results --help")
        return
    rest_crud.set_current_sub_command(command)
    if name == "cur":
        name = user_data.get_meta(meta_key)
    is_id = tools.is_id(name)
    # avoid to make two requests if we have not id.
    if command == "ls":
        tools.ls(name, is_id, __resolver)
        return

    __id = tools.get_id(name, __resolver, is_id)

    if command == "use":
        tools.use(__id, meta_key, __resolver)
        return

    if not __id:
        __id = user_data.get_meta_required(meta_key)

    system_exit = {'message': '', 'code': 0}
    if command == "summary":
        system_exit = summary(__id)
    elif command == "junitsla":
        junit(__id, junit_file)
    elif command == "delete":
        delete(__id)
        user_data.set_meta(meta_key, None)
    else:
        json_data = load_from_file(file) if file else create_json(rename, description, quality_status)
        if command == "put":
            put(__id, json_data)
        elif command == "patch":
            patch(__id, json_data)
    if command != "delete":
        user_data.set_meta(meta_key, __id)

    tools.system_exit(system_exit)


def delete(__id):
    rep = tools.delete(get_end_point(), __id, "test results")
    print(rep.text)


def put(__id, json_data):
    json_data = set_empty_fields_with_blank(json_data)
    rep = rest_crud.put(get_end_point(__id), json_data)
    tools.get_id_and_print_json(rep)


def patch(__id, json_data):
    rep = rest_crud.patch(get_end_point(__id), json_data)
    tools.get_id_and_print_json(rep)


def set_empty_fields_with_blank(json_data):
    if 'description' not in json_data:
        json_data['description'] = ''
    if 'qualityStatus' not in json_data:
        json_data['qualityStatus'] = ''
    return json_data


def junit(__id, junit_file):
    json_result = rest_crud.get(get_end_point(__id))
    json_sla_test = rest_crud.get(get_end_point(__id, __operation_sla_test))
    json_sla_interval = rest_crud.get(get_end_point(__id, __operation_sla_interval))
    displayer.print_result_junit(json_result, json_sla_test, json_sla_interval, junit_file)


def get_id_by_name_or_id(name):
    if name == "cur":
        name = user_data.get_meta(meta_key)
    is_id = tools.is_id(name)

    __id = tools.get_id(name, __resolver, is_id)

    if not __id:
        __id = user_data.get_meta_required(meta_key)

    return __id


def get_sla_data_by_name_or_id(name):
    __id = get_id_by_name_or_id(name)

    json_result = rest_crud.get(get_end_point(__id))
    status = json_result['status']
    json_sla_global = [] if status != 'TERMINATED' else rest_crud.get(get_end_point(__id, __operation_sla_global))
    json_sla_test = [] if status != 'TERMINATED' else rest_crud.get(get_end_point(__id, __operation_sla_test))
    json_sla_interval = rest_crud.get(get_end_point(__id, __operation_sla_interval))
    json_stats = rest_crud.get(get_end_point(__id, __operation_statistics))
    return {
        'id': __id,
        'result': json_result,
        'stats': json_stats,
        'sla_global': json_sla_global,
        'sla_test': json_sla_test,
        'sla_interval': json_sla_interval
    }


def summary(__id):
    json_result = rest_crud.get(get_end_point(__id))
    json_sla_global = rest_crud.get(get_end_point(__id, __operation_sla_global))
    json_sla_test = rest_crud.get(get_end_point(__id, __operation_sla_test))
    json_sla_interval = rest_crud.get(get_end_point(__id, __operation_sla_interval))
    json_stats = rest_crud.get(get_end_point(__id, __operation_statistics))
    displayer.print_result_summary(json_result, json_sla_global, json_sla_test, json_sla_interval, json_stats)
    return exit_process(json_result, json_sla_global, json_sla_test, json_sla_interval)


def get_id(name, is_id):
    if is_id or not name:
        return name
    else:
        return __resolver.resolve_name(name)


def get_end_point(id_test: str = None, operation=''):
    slash_id_test = '' if id_test is None else '/' + id_test
    return rest_crud.base_endpoint_with_workspace() + __endpoint + slash_id_test + operation


def create_json(name, description, quality_status):
    data = {}
    if name is not None:
        data['name'] = name
    if description is not None:
        data['description'] = description
    if quality_status is not None:
        data['qualityStatus'] = quality_status
    if len(data) == 0 and sys.stdin.isatty():
        for field in ['name', 'description', 'qualityStatus']:
            data[field] = input(field)
    return data


def exit_process(json_data, json_sla_global, json_sla_test, json_sla_interval):
    sla_failure_count = len(list(filter(lambda sla: sla['status'] == "FAILED", json_sla_global)))
    sla_failure_count += len(list(filter(lambda sla: sla['status'] == "FAILED", json_sla_test)))
    sla_failure_count += len(list(filter(lambda sla: sla['status'] == "FAILED", json_sla_interval)))
    term_reason = json_data['terminationReason']

    if term_reason == "FAILED_TO_START":
        return {'message': "Test failed to start.", 'code': 2}
    elif term_reason == "CANCELLED":
        return {'message': "Test cancelled.", 'code': 2}
    elif term_reason == "MANUAL":
        return {'message': "Test was stopped manually.", 'code': 2}
    elif term_reason == "LG_AVAILABILITY":
        return {'message': "Test failed due to load generator availability.", 'code': 2}
    elif term_reason == "LICENSE":
        return {'message': "Test failed because of license.", 'code': 2}
    elif term_reason == "UNKNOWN":
        return {'message': "Test failed for an unknown reason. Check logs.", 'code': 2}
    elif term_reason == "RESERVATION_ENDED":
        return {'message': "Test was stopped because the reservation ended.", 'code': 2}
    elif sla_failure_count > 0:
        return {'message': f'Test completed with {sla_failure_count} SLAs failures.', 'code': 1}
    elif term_reason == "POLICY":
        return {'message': "Test completed.", 'code': 0}
    elif term_reason == "VARIABLE":
        return {'message': "Test completed variably.", 'code': 0}
    else:
        return {'message': f'Unknown terminationReason: {term_reason}', 'code': 2}
