import neoload_cli_lib.rest_crud as rest_crud
from neoload_cli_lib import cli_exception


class Resolver:
    def __init__(self, endpoint):
        self.__endpoint = endpoint
        self.__map = {}

    def __fill_map(self, name=None):
        self.__map = {}
        all_element = rest_crud.get(self.__endpoint)
        json = None
        for element in all_element:
            name_ = element['name']
            self.__map[name_] = element['id']
            if name_ == name:
                json = element
        return json

    def resolve_name(self, name):
        __id = self.__map.get(name, None)
        if __id is None:
            self.__fill_map(name)
            __id = self.__map.get(name, None)
            if not __id:
                raise cli_exception.CliException(f"No id associated to the name '{name}'")
        return __id

    def resolve_name_or_json(self, name):
        __id = self.__map.get(name, None)
        if __id is None:
            __json = self.__fill_map(name)
            if __json:
                return __json
            else:
                raise cli_exception.CliException(f"No object associated to the name '{name}'")
        return __id

    def get_map(self):
        if len(self.__map) == 0:
            self.__fill_map()
        return self.__map

    def get_endpoint(self):
        return self.__endpoint
