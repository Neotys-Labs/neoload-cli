from neoload_cli_lib import user_data, rest_crud, tools
from commands import test_results
from datetime import datetime
from neoload_cli_lib.logs_traduction_map import dicotrad


def display_logs(displayed_lines, results_id):
    res = rest_crud.get(test_results.get_end_point(results_id, "/logs"))
    if res:
        for entry in res:
            content = entry['content']
            translated = dicotrad.get(content, content)
            log_line = f"{format_time(entry['timestamp']) + translated}"
            if log_line not in displayed_lines:
                print(log_line)
                displayed_lines.append(log_line)


def format_time(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000)
    return dt.strftime("%d.%m.%y %I:%M:%S %p")
