import pytest

from models.volume_manager import Volume, volume_schema, packer_schema


@pytest.fixture
def etcd_client(mocker):
    return mocker.MagicMock()


@pytest.fixture
def volume_manager(etcd_client):
    return Volume(etcd_client)


@pytest.fixture
def volume_manager_all(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'all')


@pytest.fixture
def key_getter(mocker, volume_manager):
    return mocker.patch.object(volume_manager, 'get_id_from_key')


@pytest.fixture
def unpacker(mocker, volume_manager):
    return mocker.patch.object(volume_manager, '_unpack')


@pytest.fixture
def etcd_dir_result(mocker):
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


@pytest.fixture
def volume_schema_loads(mocker):
    return mocker.patch.object(volume_schema, 'loads')


@pytest.fixture
def volume_schema_dumps(mocker):
    return mocker.patch.object(volume_schema, 'dumps')


@pytest.fixture
def packer_schema_loads(mocker):
    return mocker.patch.object(packer_schema, 'loads')


@pytest.fixture
def packer_schema_dumps(mocker):
    return mocker.patch.object(packer_schema, 'dumps')


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
