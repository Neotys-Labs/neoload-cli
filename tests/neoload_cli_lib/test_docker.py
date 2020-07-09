import tempfile
import unittest
from unittest import mock

import docker
import requests
from docker.models.containers import ContainerCollection

from neoload_cli_lib import config_global
from neoload_cli_lib import docker_lib
from neoload_cli_lib.cli_exception import CliException
from neoload_cli_lib.user_data import UserData


class MockImage:
    def __init__(self, i):
        self.name = i
        self.id = i


class MockContainer:
    count = 0

    def __init__(self, dict):
        name = dict.get('name')
        self.name = name
        self.id = name
        self.args = dict
        self.attrs = {}

    def reload(self):
        MockContainer.count += 1
        self.attrs = {'NetworkSettings':{'IPAddress': ('172.17.0.'+str(MockContainer.count))}}


class MockDocker:
    def __init__(self):
        self.containers = {}
        self.images = {}


class LgContainerMock:
    def reload(self):
        pass

    def __init__(self, ip):
        self.attrs = {'NetworkSettings': {'IPAddress': ip}}
        self.name = ip.replace('.', '_')


# Because Mock doesn't support name as native.
class MockName:
    def __init__(self, name):
        self.name = name


class TestMethods(unittest.TestCase):
    """ Class for executing unittest test cases """

    @mock.patch('requests.get', mock.Mock(
        side_effect=lambda k: {'aurl': 'a response', 'burl': 'b response'}.get(k, 'unhandled request %s' % k)))
    def test_mock(self):
        print(requests.get("aurl"))

    @mock.patch('neoload_cli_lib.docker_lib.get_zone', mock.Mock(
        side_effect=lambda k: {'default_zone': {'type': 'STATIC'}}.get(k, 'unhandled request %s' % k)))
    def test_get_zone(self):
        docker_lib.check_zone("default_zone")

    @mock.patch('neoload_cli_lib.docker_lib.get_zone', mock.Mock(
        side_effect=lambda k: {'default_zone': {'type': 'STATIC', 'controller': 1}}.get(k, 'unhandled request %s' % k)))
    def test_get_zone_fail_other_controller(self):
        with self.assertRaises(CliException):
            docker_lib.check_zone("default_zone")

    @mock.patch('neoload_cli_lib.docker_lib.get_zone', mock.Mock(side_effect=lambda k: {'defaultzone': {'type': 'DYNAMIC'}}.get(k, 'unhandled request %s' % k)))
    def test_get_zone2(self):
        with self.assertRaises(CliException):
            docker_lib.check_zone("defaultzone")



    @mock.patch('neoload_cli_lib.user_data.get_user_data', mock.Mock(return_value=UserData(desc={'url': "http://MyUrl", 'token': "mytoken"})))
    def test_generate_conf_lg(self):
        assert docker_lib.generate_conf_lg("mytest") == {'env': {'NEOLOADWEB_URL': 'http://MyUrl', 'NEOLOADWEB_TOKEN': 'mytoken', 'ZONE': 'mytest'}, 'name_prefix': 'lg'}

    @mock.patch('neoload_cli_lib.user_data.get_user_data', mock.Mock(return_value=UserData(desc={'url': "http://MyUrl", 'token': "mytoken"})))
    def test_generate_conf_ctrl(self):
        assert docker_lib.generate_conf_ctrl("mytest", [LgContainerMock('1.2.3.4'), LgContainerMock('3.2.1.4')]) == {'env': {'MODE': 'Managed', 'NEOLOADWEB_URL': 'http://MyUrl', 'NEOLOADWEB_TOKEN': 'mytoken', 'ZONE': 'mytest'}, 'name_prefix': 'ctrl', 'hosts': {'1_2_3_4': '1.2.3.4', '3_2_1_4': '3.2.1.4'}}




    @mock.patch('neoload_cli_lib.config_global.get_config_file', mock.Mock(return_value=tempfile.gettempdir() + "/" + next(tempfile._get_candidate_names())))
    def test_docker_install_hooks(self):
        config_global.reset()

        # settings is empty
        assert None is config_global.get_attr("$hooks.test.start", None)
        assert None is config_global.get_attr("$hooks.test.stop", None)

        # install Hooks
        docker_lib.install()
        assert "neoload_cli_lib.docker_lib.hook_test_start" in config_global.get_attr("$hooks.test.start", [])
        assert "neoload_cli_lib.docker_lib.hook_test_stop" in config_global.get_attr("$hooks.test.stop", [])

        # remove Hooks
        docker_lib.uninstall()
        assert "neoload_cli_lib.docker_lib.hook_test_start" not in config_global.get_attr("$hooks.test.start", [])
        assert "neoload_cli_lib.docker_lib.hook_test_stop" not in config_global.get_attr("$hooks.test.stop", [])



    @mock.patch('neoload_cli_lib.config_global.get_config_file', mock.Mock(return_value=tempfile.gettempdir() + "/" + next(tempfile._get_candidate_names())))
    @mock.patch('neoload_cli_lib.user_data.get_user_data', mock.Mock(return_value=UserData(desc={'url': "http://MyUrl", 'token': "mytoken"})))
    @mock.patch('neoload_cli_lib.docker_lib.get_zone', mock.Mock(side_effect=lambda k: {'defaultzone': {'type': 'STATIC'}}.get(k, 'unhandled request %s' % k)))
    @mock.patch('neoload_cli_lib.docker_lib.max_number', mock.Mock(return_value=5))
    @mock.patch('socket.gethostname',mock.Mock(return_value='Test-machine'))
    def test_docker_up(self):
        client_mock = mock.MagicMock(spec=docker.DockerClient)
        docker_lib.set_client(client_mock)
        config_global.reset()
        images = mock.MagicMock(spec=docker.models.images.ImageCollection)
        images.get.side_effect = docker.errors.ImageNotFound("not found")
        images.pull.side_effect = lambda k: MockImage(k)
        client_mock.images = images
        client_mock.containers.run.side_effect = lambda **k: MockContainer(k)
        docker_lib.up(True)
        calls = [mock.call(image='neotys/neoload-loadgenerator:latest', name='lg-6-test-machine', hostname='lg-6-test-machine',
                           labels={'launched-by-neoload-cli': 'manual'}, detach=True, extra_hosts={}, auto_remove=True,
                           environment={'NEOLOADWEB_URL': 'http://MyUrl', 'NEOLOADWEB_TOKEN': 'mytoken',
                                        'ZONE': 'defaultzone'}),
                 mock.call(image='neotys/neoload-loadgenerator:latest', name='lg-7-test-machine', hostname='lg-7-test-machine',
                           labels={'launched-by-neoload-cli': 'manual'}, detach=True, extra_hosts={}, auto_remove=True,
                           environment={'NEOLOADWEB_URL': 'http://MyUrl', 'NEOLOADWEB_TOKEN': 'mytoken',
                                        'ZONE': 'defaultzone'}),
                 mock.call(image='neotys/neoload-controller:latest', name='ctrl-6-test-machine', hostname='ctrl-6-test-machine',
                           labels={'launched-by-neoload-cli': 'manual'}, detach=True,
                           extra_hosts={'lg-6-test-machine': '172.17.0.1', 'lg-7-test-machine': '172.17.0.2'}, auto_remove=True,
                           environment={'MODE': 'Managed', 'NEOLOADWEB_URL': 'http://MyUrl',
                                        'NEOLOADWEB_TOKEN': 'mytoken', 'ZONE': 'defaultzone'})]
        client_mock.containers.run.assert_has_calls(calls)
        images_calls = [mock.call('neotys/neoload-loadgenerator:latest'), mock.call('neotys/neoload-controller:latest')]
        images.get.assert_has_calls(images_calls)
        images.pull.assert_has_calls(images_calls)
        assert docker_lib.get_setting(docker_lib.DOCKER_LAUNCHED) == ['lg-6-test-machine', 'lg-7-test-machine', 'ctrl-6-test-machine']


    @mock.patch('neoload_cli_lib.config_global.get_config_file', mock.Mock(return_value=tempfile.gettempdir() + "/" + next(tempfile._get_candidate_names())))
    def test_docker_down(self):
        mock_client = mock.MagicMock(spec=docker.DockerClient)
        docker_lib.set_client(mock_client)
        config_global.reset()
        docker_lib.add_set(docker_lib.DOCKER_LAUNCHED, ["id_1", "id_2"])
        mock_id_1 = mock.Mock()
        mock_id_2 = mock.Mock()
        mock_client.containers.get.side_effect = lambda k: {'id_1': mock_id_1, 'id_2': mock_id_2}.get(k, 'unhandled request %s' % k)
        docker_lib.down()
        mock_id_1.stop.has_called_once()
        mock_id_2.stop.has_called_once()
        assert docker_lib.get_setting(docker_lib.DOCKER_LAUNCHED) == []

    def test_max_number(self):
        client_mock = mock.MagicMock(spec=docker.DockerClient)
        docker_lib.set_client(client_mock)
        client_mock.containers.list.return_value = [MockName('lg-1-a'), MockName('lg-2-a'), MockName('dg-3-a')]
        i = docker_lib.max_number("lg")
        assert i == 2
        client_mock.containers.list.assert_has_calls([mock.call(all=True)])

    @mock.patch('neoload_cli_lib.config_global.get_config_file',
                mock.Mock(return_value=tempfile.gettempdir() + "/" + next(tempfile._get_candidate_names())))
    @mock.patch('commands.zones.get_zones', mock.Mock(
        return_value=[{'id': 'aze', 'type': 'STATIC', 'loadgenerators': [], 'controllers': []},
                      {'id': 'toto', 'type': 'DYNAMIC'}]))
    def test_start_hook(self):
        with mock.patch('neoload_cli_lib.docker_lib.start_infra', return_value=None) as mock_method:
            config_global.reset()
            config_global.set_attr(docker_lib.DOCKER_ZONE, "aze")
            docker_lib.hook_test_start({'controllerZoneId': 'aze', 'lgZoneIds': {'aze': 2}})
            mock_method.assert_has_calls([mock.call('aze', 1, 2, False, None)])

