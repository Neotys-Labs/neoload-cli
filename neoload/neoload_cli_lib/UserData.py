import pyconfig


class UserData:
    __conf_name = "neoload-cli-v1"

    def __init__(self, token: str, url: str):
        self.token = token
        self.url = url

    @staticmethod
    def do_login(token, url):
        if token is None:
            raise Exception('token is mandatory. please see neoload login --help.')
        user_data = UserData(token, url)
        pyconfig.set(UserData.__conf_name, user_data)
        return user_data

    @staticmethod
    def do_logout():
        pyconfig.set(UserData.__conf_name, None)

    @staticmethod
    def get_login():
        user_data = pyconfig.get(UserData.__conf_name)
        if user_data is None:
            raise Exception("You are'nt logged. Please use \"command neoload login\" first")
        return user_data
