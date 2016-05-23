import etcd
import pytest

from pytest_mock import mock_module

from models.volume_manager import Volume, volume_schema, packer_schema


class TestVolumeManager:
    def test_volume_key(self):
        assert Volume.KEY == 'volumes'

    def test_volume_all_key_not_found(self, mocker):
        etcd_mock = mocker.MagicMock()
        etcd_mock.read = mocker.MagicMock(side_effect=etcd.EtcdKeyNotFound)

        volume_manager = Volume(etcd_mock)
        volumes = volume_manager.all()

        assert volumes == []
        etcd_mock.read.assert_called_with(volume_manager.KEY)

    def test_volume_all_keys_except_the_dir(self, mocker):
        etcd_mock = mocker.MagicMock()
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

        # prepare result
        etcd_mock.read = mocker.MagicMock(return_value=dir_mock)

        # leaves property mock
        leaves_mock = mocker.PropertyMock(return_value=[dir_mock, entry_mock])
        type(dir_mock).leaves = leaves_mock

        # object to test
        volume_manager = Volume(etcd_mock)

        # stub out unpacker
        unpacker = mocker.patch.object(volume_manager, '_unpack')
        unpacker.return_value = [entry_mock]

        # run
        volumes = volume_manager.all()

        # make the needed assertions
        unpacker.assert_called_with([entry_mock])
        assert volumes == [entry_mock]
        etcd_mock.read.assert_called_with(volume_manager.KEY)

    def test_volume_by_id_key_not_found(self, mocker):
        etcd_mock = mocker.MagicMock()
        etcd_mock.read = mocker.MagicMock(side_effect=etcd.EtcdKeyNotFound)

        volume_manager = Volume(etcd_mock)
        volume = volume_manager.by_id('1')

        assert volume is None
        etcd_mock.read.assert_called_with('/{}/{}'.format(volume_manager.KEY, '1'))

    def test_volume_by_id(self, mocker):
        etcd_mock = mocker.MagicMock()
        etcd_result_mock = mocker.MagicMock()
        etcd_mock.read = mocker.MagicMock(side_effect=etcd_result_mock)

        volume_manager = Volume(etcd_mock)

        # stub out unpacker
        unpacker = mocker.patch.object(volume_manager, '_unpack')
        unpacker.return_value = [etcd_result_mock]

        volume = volume_manager.by_id('1')

        assert volume == etcd_result_mock
        etcd_mock.read.assert_called_with('/{}/{}'.format(volume_manager.KEY, '1'))

    def test_volume_by_state_no_data(self, mocker):
        etcd_mock = mocker.MagicMock()

        volume_manager = Volume(etcd_mock)

        # stub out all()
        all_query_mock = mocker.patch.object(volume_manager, 'all')
        all_query_mock.return_value = []

        volumes = volume_manager.by_state('NONE')

        assert volumes == []
        assert all_query_mock.called

    def test_volume_by_state_with_data_none_matching(self, mocker):
        etcd_mock = mocker.MagicMock()

        volume_manager = Volume(etcd_mock)

        # stub out all()
        all_query_mock = mocker.patch.object(volume_manager, 'all')

        data = mocker.MagicMock(unpacked_value={'state': 'ready'})
        all_query_mock.return_value = [data]

        volumes = volume_manager.by_state('NONE')

        assert volumes == []
        assert all_query_mock.called

    def test_volume_by_state_with_data_with_matching(self, mocker):
        etcd_mock = mocker.MagicMock()
        volume_manager = Volume(etcd_mock)

        # stub out all()
        all_query_mock = mocker.patch.object(volume_manager, 'all')

        data = mocker.MagicMock(unpacked_value={'state': 'ready'})
        matchable_data = mocker.MagicMock(unpacked_value={'state': 'NONE'})
        all_query_mock.return_value = [data, matchable_data, data]

        volumes = volume_manager.by_state('NONE')

        assert volumes == [matchable_data]
        assert all_query_mock.called

    def test_volume_create(self, mocker):
        etcd_mock = mocker.MagicMock()
        volume_manager = Volume(etcd_mock)

        data = {
            'name': 'test',
            'value': ''
        }

        dumps_mock = mocker.patch.object(packer_schema, 'dumps')
        dumps_mock.return_value = ('{"name": "test", "value": ""}', {})

        etcd_result_mock = mocker.MagicMock(name='', value='{"name": "test", "value": ""}')
        etcd_mock.write.return_value = etcd_result_mock

        unpacker = mocker.patch.object(volume_manager, '_unpack')
        unpacker.return_value = [etcd_result_mock]

        result = volume_manager.create(data)

        dumps_mock.assert_called_with(data)
        etcd_mock.write.assert_called_with(Volume.KEY, dumps_mock.return_value[0], append=True)
        unpacker.assert_called_with([etcd_result_mock])
        assert result == etcd_result_mock

    @pytest.mark.parametrize('error', [etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound])
    def test_volume_update_etcd_errors(self, error, mocker):
        etcd_mock = mocker.MagicMock()
        volume_manager = Volume(etcd_mock)

        dumps_mock = mocker.patch.object(packer_schema, 'dumps')
        dumps_mock.return_value = ({'name': 'test'}, {})

        etcd_mock.update.side_effect = error

        volume = mocker.MagicMock()
        unpacked_value = mocker.PropertyMock(return_value={})
        type(volume).unpacked_value = unpacked_value

        output_volume = volume_manager.update(volume)

        assert not output_volume
        assert etcd_mock.update.called

    def test_volume_update_etcd(self, mocker):
        class DummyVolume:
            def __init__(self, value, unpacked_value):
                self.value = value
                self.unpacked_value = unpacked_value
                self.key = '/volumes/1'

        etcd_mock = mocker.MagicMock()
        volume_manager = Volume(etcd_mock)

        dumps_mock = mocker.patch.object(packer_schema, 'dumps')
        dumps_mock.return_value = ({'name': 'test'}, {})

        volume = DummyVolume(value='{"name": "test"}', unpacked_value={'name': 'test'})
        etcd_mock.update.return_value = volume

        unpacker = mocker.patch.object(volume_manager, '_unpack')
        unpacker.return_value = [volume]

        key_getter = mocker.patch.object(volume_manager, 'get_id_from_key')
        key_getter.return_value = '1'

        output_volume = volume_manager.update(volume)

        assert output_volume
        assert output_volume.unpacked_value['id'] == '1'
        key_getter.assert_called_once_with('/volumes/1')

    def test_volume_unpack(self, mocker):
        etcd_mock = mocker.MagicMock()
        volume_manager = Volume(etcd_mock)

        data_mock_1 = mocker.MagicMock(value='')
        data_mock_2 = mocker.MagicMock(value='{"name": "test"}')

        loads_mock = mocker.patch.object(volume_schema, 'loads')
        loads_mock.side_effect = [({}, {}), ({'name': 'test'}, {}), RuntimeError]

        volume_manager._unpack([data_mock_1, data_mock_2])

        loads_mock.assert_has_calls([mock_module.call(data_mock_1.value), mock_module.call(data_mock_2.value)])
        assert data_mock_1.unpacked_value == {}
        assert data_mock_2.unpacked_value == {'name': 'test'}

    def test_volume_get_id_from_key_invalid_input(self):
        key = 'volumes'

        assert Volume.get_id_from_key(key) == ''

    def test_volume_get_id_from_key(self):
        key = '/volumes/1'

        assert Volume.get_id_from_key(key) == '1'
