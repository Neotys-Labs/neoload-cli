from neoload_cli_lib.UserData import UserData


class TestUserData:
    def test_login(self):
        login = UserData.do_login('abcdefghf201df15d897e7afe99a24159da764c7cc82b2ab',
                                  'https://preprod-neoload.saas.neotys.com/')
        assert login.token == UserData.get_login().token
        assert login.url == UserData.get_login().url
        assert UserData.get_login().token == 'abcdefghf201df15d897e7afe99a24159da764c7cc82b2ab'
        assert UserData.get_login().url == 'https://preprod-neoload.saas.neotys.com/'

    def test_logout(self):
        UserData.do_login('some token', 'some url')
        UserData.do_logout()
        assert UserData.get_login() is None
