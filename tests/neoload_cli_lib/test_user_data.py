import pytest
import neoload_cli_lib.user_data as user_data


@pytest.mark.authentication
class TestUserData:
    def test_login(self):
        login = user_data.do_login('abcdefghf201df15d897e7afe99a24159da764c7cc82b2ab',
                                  'https://preprod-neoload.saas.neotys.com/', False)
        assert login.token == user_data.get_user_data().token
        assert login.url == user_data.get_user_data().url
        assert user_data.get_user_data().token == 'abcdefghf201df15d897e7afe99a24159da764c7cc82b2ab'
        assert user_data.get_user_data().url == 'https://preprod-neoload.saas.neotys.com/'

    def test_login_no_write(self):
        login = user_data.do_login('abcdefghf201df15d897e7afe99a24159da764c7cc82b2ab',
                                  'https://preprod-neoload.saas.neotys.com/', True)
        assert login.token == user_data.get_user_data().token
        assert login.url == user_data.get_user_data().url
        assert user_data.get_user_data().token == 'abcdefghf201df15d897e7afe99a24159da764c7cc82b2ab'
        assert user_data.get_user_data().url == 'https://preprod-neoload.saas.neotys.com/'

    def test_login_without_token(self):
        with pytest.raises(Exception) as context:
            user_data.do_login(None, 'some url', False)
        assert 'token is mandatory. please see neoload login --help.' in str(context.value)

    def test_logout(self):
        user_data.do_login('some token', 'some url', False)
        user_data.do_logout()
        with pytest.raises(Exception) as context:
            user_data.get_user_data()
        assert 'You are\'nt logged. Please use command "neoload login" first' in str(context.value)
