import pytest
from neoload_cli_lib import UserData


@pytest.mark.authentication
class TestUserData:
    def test_login(self):
        login = UserData.do_login('abcdefghf201df15d897e7afe99a24159da764c7cc82b2ab',
                                  'https://preprod-neoload.saas.neotys.com/', False)
        assert login.token == UserData.get_login().token
        assert login.url == UserData.get_login().url
        assert UserData.get_login().token == 'abcdefghf201df15d897e7afe99a24159da764c7cc82b2ab'
        assert UserData.get_login().url == 'https://preprod-neoload.saas.neotys.com/'

    def test_login_no_write(self):
        login = UserData.do_login('abcdefghf201df15d897e7afe99a24159da764c7cc82b2ab',
                                  'https://preprod-neoload.saas.neotys.com/', True)
        assert login.token == UserData.get_login().token
        assert login.url == UserData.get_login().url
        assert UserData.get_login().token == 'abcdefghf201df15d897e7afe99a24159da764c7cc82b2ab'
        assert UserData.get_login().url == 'https://preprod-neoload.saas.neotys.com/'

    def test_login_without_token(self):
        with pytest.raises(Exception) as context:
            UserData.do_login(None, 'some url', False)
        assert 'token is mandatory. please see neoload login --help.' in str(context.value)

    def test_logout(self):
        UserData.do_login('some token', 'some url', False)
        UserData.do_logout()
        with pytest.raises(Exception) as context:
            UserData.get_login()
        assert 'You are\'nt logged. Please use command "neoload login" first' in str(context.value)
