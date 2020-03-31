import unittest

from neoload_cli_lib.UserData import UserData


class TestUserData(unittest.TestCase):
    def test_login(self):
        login = UserData.do_login('abcdefghf201df15d897e7afe99a24159da764c7cc82b2ab',
                                  'https://preprod-neoload.saas.neotys.com/')
        assert login.token == UserData.get_login().token
        assert login.url == UserData.get_login().url
        assert UserData.get_login().token == 'abcdefghf201df15d897e7afe99a24159da764c7cc82b2ab'
        assert UserData.get_login().url == 'https://preprod-neoload.saas.neotys.com/'

    def test_login_without_token(self):
        with self.assertRaises(Exception) as context:
            UserData.do_login(None, 'some url')
        self.assertTrue('token is mandatory. please see neoload login --help.' in context.exception.args)

    def test_logout(self):
        UserData.do_login('some token', 'some url')
        UserData.do_logout()
        with self.assertRaises(Exception) as context:
            UserData.get_login()
        self.assertTrue('You are\'nt logged. Please use "command neoload login" first' in context.exception.args)
