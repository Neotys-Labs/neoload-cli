import click
from neoload_cli_lib import rest_crud, tools


@click.command()
@click.argument("name_or_id", type=str, required=False)
@click.option("--human", "-h", is_flag=True, help="display resources for human")
@click.option("--static/--dynamic", "static_dynamic", default=None, help="filter for dynamic or static zones")
def cli(name_or_id, static_dynamic, human):
    """read of NeoLoad Web zones"""
    resp = rest_crud.get("/v2/resources/zones")
    resp = [elem for elem in resp if filter_result(elem, name_or_id, static_dynamic)]
    if human:
        print_human(resp)
    else:
        tools.print_json(resp)


def print_human(resp):
    print("TYPE\tID\tNAME")
    for element in resp:
        print(f"{element['type']}\t{element['id']}\t{element['name']}")
        display_human_sub(element['controllers'], "Controllers")
        display_human_sub(element['loadgenerators'], "Load Generator")
        print()


def display_human_sub(elements, title):
    print(f"*\t{title} ({len(elements)})")
    for element in elements:
        print(f"+\t\t{element['name']}\t{element['version']}\t{element['status']}\t")


def filter_result(elem, name_or_id, static):
    if static is not None:
        type_infra = 'STATIC' if static else 'DYNAMIC'
        if elem['type'] != type_infra:
            return False
    if name_or_id and elem['name'] != name_or_id and elem['id'] != name_or_id:
        return False

    return True
