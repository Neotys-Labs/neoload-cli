import neoload_cli_lib.rest_crud as rest_crud
from neoload_cli_lib import cli_exception


class Resolver:
    def __init__(self, endpoint, get_base_endpoint):
        self.__endpoint = endpoint
        self.__get_base_endpoint = get_base_endpoint
        self.__map = {}

    def __fill_map(self, ws, name=None):
        all_element = rest_crud.get_with_pagination(self.get_endpoint())
        json = None
        ws_map = {}
        self.__map[ws] = ws_map
        for element in all_element:
            name_ = element['name']
            ws_map[name_] = element['id']
            if name_ == name:
                json = element
        return json

    def resolve_name(self, name, return_none=False):
        ws = str(rest_crud.get_workspace())
        __id = self.__map.get(ws, {}).get(name, None)
        if __id is None:
            self.__fill_map(ws, name)
            __id = self.__map.get(ws, {}).get(name, None)
            if not __id and not return_none:
                raise cli_exception.CliException(f"No id associated to the name '{name}'")
        return __id

    def resolve_name_or_json(self, name):
        ws = str(rest_crud.get_workspace())
        __id = self.__map.get(ws, {}).get(name, None)
        if __id is None:
            __json = self.__fill_map(ws, name)
            if __json:
                return __json
            else:
                raise cli_exception.CliException(f"No object associated to the name '{name}'")
        return __id

    def get_map(self):
        ws = str(rest_crud.get_workspace())
        if len(self.__map) == 0:
            self.__fill_map(ws)
        return self.__map[ws]

    def get_endpoint(self):
        return self.__get_base_endpoint() + self.__endpoint
