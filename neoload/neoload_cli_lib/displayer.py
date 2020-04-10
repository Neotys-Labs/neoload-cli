from neoload_cli_lib import tools


def print_result_summary(json_result, json_sla_global, json_sla_test, json_sla_interval, json_stats):
    tools.print_json(json_result)
    tools.print_json(json_sla_global)
    tools.print_json(json_sla_test)
    tools.print_json(json_sla_interval)
    tools.print_json(json_stats)
