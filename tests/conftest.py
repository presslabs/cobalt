from pytest import fixture

from api import Api
from models.manager import VolumeManager, MachineManager


@fixture
def m_etcd_client(mocker):
    return mocker.MagicMock()


@fixture
def p_etcd_client_read(mocker, m_etcd_client):
    return mocker.patch.object(m_etcd_client, 'read')


@fixture
def p_etcd_client_update(mocker, m_etcd_client):
    return mocker.patch.object(m_etcd_client, 'update')


@fixture
def p_etcd_client_write(mocker, m_etcd_client):
    return mocker.patch.object(m_etcd_client, 'write')


@fixture
def volume_manager(m_etcd_client):
    return VolumeManager(m_etcd_client)


@fixture
def p_volume_manager_all(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'all')


@fixture
def p_volume_manager_all_keys(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'all_keys')


@fixture
def p_volume_manager_by_id(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'by_id')


@fixture
def p_volume_manager_by_node(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'by_node')


@fixture
def p_volume_manager_update(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'update')


@fixture
def p_volume_manager_watch(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'watch')


@fixture
def p_volume_manager_get_lock(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'get_lock')


@fixture
def p_volume_manager_filter_states(mocker):
    return mocker.patch('models.volume_manager.VolumeManager.filter_states')


@fixture
def p_key_getter(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'get_id_from_key')


@fixture
def p_load_from_etcd(mocker, volume_manager):
    return mocker.patch.object(volume_manager, '_load_from_etcd')


@fixture
def p_json_dumps(mocker):
    return mocker.patch('flask.json.dumps')


@fixture
def p_json_loads(mocker):
    return mocker.patch('flask.json.loads')


@fixture
def machine_manager(m_etcd_client):
    return MachineManager(m_etcd_client)


@fixture
def p_machine_manager_all(mocker, machine_manager):
    return mocker.patch.object(machine_manager, 'all')


@fixture
def p_machine_manager_by_id(mocker, machine_manager):
    return mocker.patch.object(machine_manager, 'by_id')


@fixture
def p_machine_manager_update(mocker, machine_manager):
    return mocker.patch.object(machine_manager, 'update')


@fixture
def p_machine_manager_all_keys(mocker, machine_manager):
    return mocker.patch.object(machine_manager, 'all_keys')


@fixture
def p_machine_manager_create(mocker, machine_manager):
    return mocker.patch.object(machine_manager, 'create')


@fixture
def p_etcd_lock(mocker):
    return mocker.patch('etcd.Lock')


@fixture
def m_etcd_dir_result(mocker):
    entry_mock = mocker.MagicMock(
        dir=False,
        key=2,
        value='{"name":"test"}'
    )
    dir_mock = mocker.MagicMock(
        dir=True,
        key=1,
        value='{}',
        _children=[entry_mock]
    )

    # leaves property mock
    leaves_mock = mocker.PropertyMock(return_value=[dir_mock, entry_mock])
    type(dir_mock).leaves = leaves_mock

    return dir_mock, entry_mock


@fixture
def flask_app(volume_manager):
    return Api._create_app(volume_manager, testing=True)


@fixture
def p_print(mocker):
    return mocker.patch('builtins.print')


class Dummy:
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            self.__setattr__(key, val)


dummy_ready_volume = Dummy(value={'name': 'test', 'state': 'ready', 'control': {'parent_id': ''}},
                           value_json='{"name": "test", "state": "ready", "control": {"parent_id": ""}}',
                           key='/volumes/1')

dummy_invalid_state_volume = Dummy(value={'name': 'test', 'state': 'NONE', 'control': {'parent_id': ''}},
                                   value_json='{"name": "test", "state": "NONE", "control": {"parent_id": ""}}',
                                   key='/volumes/2')

dummy_machines = [Dummy(value={},
                        value_json='{}',
                        key='/machines/1'),
                  Dummy(value={},
                        value_json='{}',
                        key='/machines/2')]
