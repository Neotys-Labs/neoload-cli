import pyconfig


class UserData:
    __conf_name = "neoload-cli-v2"
    __user_data_singleton = pyconfig.get(__conf_name)

    def __init__(self, token: str, url: str):
        self.token = token
        self.url = url

    @staticmethod
    def do_login(token, url="https://neoload-api.saas.neotys.com/"):
        user_data = UserData(token, url)
        pyconfig.set(UserData.__conf_name, user_data)
        UserData.__user_data_singleton = user_data
        return user_data

    @staticmethod
    def do_logout():
        pyconfig.set(UserData.__conf_name, None)

    @staticmethod
    def get_login():
        if UserData.__user_data_singleton is None:
            raise Exception("You are'nt logged. Please use \"command neoload login\" first")
        return UserData.__user_data_singleton
