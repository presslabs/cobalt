import etcd

from pytest import mark

from pytest_mock import mock_module

from models import VolumeManager
from tests.conftest import dummy_invalid_state_volume, dummy_ready_volume


class TestVolumeManager:
    def test_volume_key(self):
        assert VolumeManager.KEY == 'volumes'

    def test_volume_all_key_not_found(self, p_etcd_client_read, m_volume_manager):
        p_etcd_client_read.side_effect = etcd.EtcdKeyNotFound

        volumes = m_volume_manager.all()

        assert volumes == []
        p_etcd_client_read.assert_called_with(VolumeManager.KEY, sorted=True)

    def test_volume_all_keys_except_the_dir(self, m_etcd_dir_result, p_etcd_client_read, p_unpacker, m_volume_manager):
        dir_mock, entry_mock = m_etcd_dir_result

        # prepare result
        p_etcd_client_read.return_value = dir_mock
        p_unpacker.return_value = [entry_mock]

        # run
        volumes = m_volume_manager.all()

        # make the needed assertions
        p_unpacker.assert_called_with([entry_mock])
        assert volumes == [entry_mock]
        p_etcd_client_read.assert_called_with(VolumeManager.KEY, sorted=True)

    def test_volume_by_id_key_not_found(self, m_volume_manager, p_etcd_client_read):
        p_etcd_client_read.side_effect = etcd.EtcdKeyNotFound

        volume = m_volume_manager.by_id('1')

        assert volume is None
        p_etcd_client_read.assert_called_with('/{}/{}'.format(m_volume_manager.KEY, '1'))

    def test_volume_by_id(self, p_etcd_client_read, p_unpacker, m_volume_manager, mocker):
        etcd_result_mock = mocker.MagicMock()
        p_etcd_client_read.side_effect = etcd_result_mock
        p_unpacker.return_value = [etcd_result_mock]

        volume = m_volume_manager.by_id('1')

        assert volume == etcd_result_mock
        p_etcd_client_read.assert_called_with('/{}/{}'.format(VolumeManager.KEY, '1'))

    @mark.parametrize('query,state_filter,result', [
        # all() return value, state to query, result
        ([], 'NONE', []),
        ([dummy_invalid_state_volume], 'ready', []),
        ([dummy_invalid_state_volume, dummy_ready_volume, dummy_invalid_state_volume], 'ready', [dummy_ready_volume])
    ])
    def test_volume_by_state_no_data(self, query, state_filter, result, m_volume_manager, p_volume_manager_all):
        p_volume_manager_all.return_value = query

        volumes = m_volume_manager.by_state(state_filter)

        assert volumes == result
        assert p_volume_manager_all.called

    def test_volume_create(self, p_etcd_client_write, p_packer_schema_dumps, p_unpacker, m_volume_manager, mocker):
        data = {
            'name': 'test',
            'value': ''
        }

        p_packer_schema_dumps.return_value = ('{"name": "test", "value": ""}', {})
        etcd_result_mock = mocker.MagicMock(name='', value='{"name": "test", "value": ""}')
        p_etcd_client_write.return_value = etcd_result_mock
        p_unpacker.return_value = [etcd_result_mock]

        result = m_volume_manager.create(data)

        p_packer_schema_dumps.assert_called_with(data)
        p_etcd_client_write.assert_called_with(VolumeManager.KEY, p_packer_schema_dumps.return_value[0], append=True)
        p_unpacker.assert_called_with([etcd_result_mock])
        assert result == etcd_result_mock

    @mark.parametrize('error', [etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound])
    def test_volume_update_etcd_errors(self, p_etcd_client_update, p_packer_schema_dumps, m_volume_manager, error):
        p_packer_schema_dumps.return_value = ({'name': 'test'}, {})

        p_etcd_client_update.side_effect = error
        output_volume = m_volume_manager.update(dummy_ready_volume)

        assert not output_volume
        assert p_etcd_client_update.called

    def test_volume_update_etcd(self, p_etcd_client_update, m_volume_manager, p_unpacker, p_packer_schema_dumps,
                                p_key_getter):
        p_packer_schema_dumps.return_value = ({'name': 'test'}, {})
        p_etcd_client_update.update.return_value = dummy_ready_volume
        p_unpacker.return_value = [dummy_ready_volume]
        p_key_getter.return_value = '1'

        output_volume = m_volume_manager.update(dummy_ready_volume)

        assert output_volume
        assert output_volume.unpacked_value['id'] == '1'
        p_key_getter.assert_called_once_with(dummy_ready_volume.key)

    def test_volume_unpack(self, m_volume_manager, p_volume_schema_loads, mocker):
        data_mock_1 = mocker.MagicMock(value='')
        data_mock_2 = mocker.MagicMock(value='{"name": "test"}')
        p_volume_schema_loads.side_effect = [({}, {}), ({'name': 'test'}, {}), RuntimeError]
    
        m_volume_manager._unpack([data_mock_1, data_mock_2])
    
        call = mock_module.call
        p_volume_schema_loads.assert_has_calls([call(data_mock_1.value), call(data_mock_2.value)])
        assert data_mock_1.unpacked_value == {}
        assert data_mock_2.unpacked_value == {'name': 'test'}
    
    def test_volume_get_id_from_key_invalid_input(self):
        key = 'volumes'
    
        assert VolumeManager.get_id_from_key(key) == ''
    
    def test_volume_get_id_from_key(self):
        key = '/volumes/1'
    
        assert VolumeManager.get_id_from_key(key) == '1'
