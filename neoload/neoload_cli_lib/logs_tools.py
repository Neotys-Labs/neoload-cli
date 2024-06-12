from neoload_cli_lib import user_data, rest_crud, tools
from commands import test_results
from datetime import datetime
from neoload_cli_lib.logs_traduction_map import dicotrad


def display_logs(displayed_lines, results_id):
    res = rest_crud.get(test_results.get_end_point(results_id, "/logs"))
    if res:
        log_lines = [f"{format_time(entry['timestamp'])} - {entry['content']}" for entry in res]
        for log_line in log_lines:
            if log_line not in displayed_lines:
                translated_log_line = translate_with_keywords(log_line)
                print(translated_log_line)
                displayed_lines.append(log_line)


def translate_with_keywords(log_line):
    translated_log_line = log_line
    for keyword, translation in dicotrad.items():
        if keyword in log_line:
            translated_log_line = translated_log_line.replace(keyword, translation)
    return translated_log_line


def format_time(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000)
    return dt.strftime("%d.%m.%y %I:%M:%S %p")
