import etcd
import pytest

from pytest_mock import mock_module

from models.volume_manager import Volume
from tests.conftest import dummy_invalid_state_volume, dummy_ready_volume


class TestVolumeManager:
    def test_volume_key(self):
        assert Volume.KEY == 'volumes'

    def test_volume_all_key_not_found(self, etcd_client, volume_manager, mocker):
        etcd_client.read = mocker.MagicMock(side_effect=etcd.EtcdKeyNotFound)

        volumes = volume_manager.all()

        assert volumes == []
        etcd_client.read.assert_called_with(volume_manager.KEY, sorted=True)

    def test_volume_all_keys_except_the_dir(self, etcd_dir_result, etcd_client, unpacker, volume_manager, mocker):
        dir_mock, entry_mock = etcd_dir_result

        # prepare result
        etcd_client.read = mocker.MagicMock(return_value=dir_mock)
        unpacker.return_value = [entry_mock]

        # run
        volumes = volume_manager.all()

        # make the needed assertions
        unpacker.assert_called_with([entry_mock])
        assert volumes == [entry_mock]
        etcd_client.read.assert_called_with(volume_manager.KEY, sorted=True)

    def test_volume_by_id_key_not_found(self, etcd_client, volume_manager, mocker):
        etcd_client.read = mocker.MagicMock(side_effect=etcd.EtcdKeyNotFound)

        volume = volume_manager.by_id('1')

        assert volume is None
        etcd_client.read.assert_called_with('/{}/{}'.format(volume_manager.KEY, '1'))

    def test_volume_by_id(self, etcd_client, unpacker, volume_manager, mocker):
        etcd_result_mock = mocker.MagicMock()
        etcd_client.read = mocker.MagicMock(side_effect=etcd_result_mock)
        unpacker.return_value = [etcd_result_mock]

        volume = volume_manager.by_id('1')

        assert volume == etcd_result_mock
        etcd_client.read.assert_called_with('/{}/{}'.format(volume_manager.KEY, '1'))

    @pytest.mark.parametrize('query,state_filter,result', [
        # all() return value, state to query, result
        ([], 'NONE', []),
        ([dummy_invalid_state_volume], 'ready', []),
        ([dummy_invalid_state_volume, dummy_ready_volume, dummy_invalid_state_volume], 'ready', [dummy_ready_volume])
    ])
    def test_volume_by_state_no_data(self, query, state_filter, result, volume_manager, volume_manager_all):
        volume_manager_all.return_value = query

        volumes = volume_manager.by_state(state_filter)

        assert volumes == result
        assert volume_manager_all.called

    def test_volume_create(self, etcd_client, packer_schema_dumps, unpacker, volume_manager, mocker):
        data = {
            'name': 'test',
            'value': ''
        }

        packer_schema_dumps.return_value = ('{"name": "test", "value": ""}', {})

        etcd_result_mock = mocker.MagicMock(name='', value='{"name": "test", "value": ""}')
        etcd_client.write.return_value = etcd_result_mock

        unpacker.return_value = [etcd_result_mock]

        result = volume_manager.create(data)

        packer_schema_dumps.assert_called_with(data)
        etcd_client.write.assert_called_with(Volume.KEY, packer_schema_dumps.return_value[0], append=True)
        unpacker.assert_called_with([etcd_result_mock])
        assert result == etcd_result_mock

    @pytest.mark.parametrize('error', [etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound])
    def test_volume_update_etcd_errors(self, etcd_client, packer_schema_dumps, volume_manager, error):
        packer_schema_dumps.return_value = ({'name': 'test'}, {})

        etcd_client.update.side_effect = error
        output_volume = volume_manager.update(dummy_ready_volume)

        assert not output_volume
        assert etcd_client.update.called

    def test_volume_update_etcd(self, etcd_client, volume_manager, unpacker, packer_schema_dumps, key_getter):
        packer_schema_dumps.return_value = ({'name': 'test'}, {})
        etcd_client.update.return_value = dummy_ready_volume
        unpacker.return_value = [dummy_ready_volume]
        key_getter.return_value = '1'

        output_volume = volume_manager.update(dummy_ready_volume)

        assert output_volume
        assert output_volume.unpacked_value['id'] == '1'
        key_getter.assert_called_once_with(dummy_ready_volume.key)

    def test_volume_unpack(self, volume_manager, volume_schema_loads, mocker):
        data_mock_1 = mocker.MagicMock(value='')
        data_mock_2 = mocker.MagicMock(value='{"name": "test"}')
        volume_schema_loads.side_effect = [({}, {}), ({'name': 'test'}, {}), RuntimeError]

        volume_manager._unpack([data_mock_1, data_mock_2])

        call = mock_module.call
        volume_schema_loads.assert_has_calls([call(data_mock_1.value), call(data_mock_2.value)])
        assert data_mock_1.unpacked_value == {}
        assert data_mock_2.unpacked_value == {'name': 'test'}

    def test_volume_get_id_from_key_invalid_input(self):
        key = 'volumes'

        assert Volume.get_id_from_key(key) == ''

    def test_volume_get_id_from_key(self):
        key = '/volumes/1'

        assert Volume.get_id_from_key(key) == '1'
