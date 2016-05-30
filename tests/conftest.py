from pytest import fixture

from api import Api

from models import VolumeManager, volume_schema, packer_schema, volume_attribute_schema


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
def p_volume_manager_by_id(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'by_id')


@fixture
def p_volume_manager_update(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'update')


@fixture
def p_key_getter(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'get_id_from_key')


@fixture
def p_unpacker(mocker, volume_manager):
    return mocker.patch.object(volume_manager, '_unpack')


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
def p_volume_schema_loads(mocker):
    return mocker.patch.object(volume_schema, 'loads')


@fixture
def p_volume_schema_dumps(mocker):
    return mocker.patch.object(volume_schema, 'dumps')


@fixture
def p_volume_attribute_schema_loads(mocker):
    return mocker.patch.object(volume_attribute_schema, 'loads')


@fixture
def p_volume_attribute_schema_dumps(mocker):
    return mocker.patch.object(volume_attribute_schema, 'dumps')


@fixture
def p_packer_schema_loads(mocker):
    return mocker.patch.object(packer_schema, 'loads')


@fixture
def p_packer_schema_dumps(mocker):
    return mocker.patch.object(packer_schema, 'dumps')


@fixture
def flask_app(volume_manager):
    return Api._create_app(volume_manager, testing=True)


class DummyVolume:
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            self.__setattr__(key, val)


dummy_ready_volume = DummyVolume(value='{"name": "test", "state": "ready"}',
                                 unpacked_value={'name': 'test', 'state': 'ready'},
                                 key='/volumes/1')

dummy_invalid_state_volume = DummyVolume(value='{"name": "test", "state": "NONE"}',
                                         unpacked_value={'name': 'test', 'state': 'NONE'},
                                         key='/volumes/2')
