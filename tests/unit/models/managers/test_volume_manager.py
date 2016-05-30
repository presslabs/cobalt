import etcd

from pytest import mark

from pytest_mock import mock_module

from models import VolumeManager, packer_schema
from tests.conftest import dummy_invalid_state_volume, dummy_ready_volume


class TestVolumeManager:
    def test_volume_manager_class_vars(self):
        assert VolumeManager.KEY == 'volumes'
        assert VolumeManager.SCHEMA == packer_schema

    @mark.parametrize('query,state_filter,result', [
        # all() return value, state to query, result
        ([], 'NONE', []),
        ([dummy_invalid_state_volume], 'ready', []),
        ([dummy_invalid_state_volume, dummy_ready_volume, dummy_invalid_state_volume], 'ready', [dummy_ready_volume])
    ])
    def test_volume_by_state(self, query, state_filter, result, volume_manager, p_volume_manager_all):
        p_volume_manager_all.return_value = query

        volumes = volume_manager.by_state(state_filter)

        assert volumes == result
        assert p_volume_manager_all.called

    def test_volume_update_etcd(self, p_etcd_client_update, volume_manager, p_unpacker, p_key_getter,
                                p_packer_schema_dumps):
        p_packer_schema_dumps.return_value = ({'name': 'test'}, {})
        p_etcd_client_update.update.return_value = dummy_ready_volume
        p_unpacker.return_value = [dummy_ready_volume]
        p_key_getter.return_value = '1'

        output_volume = volume_manager.update(dummy_ready_volume)

        assert output_volume
        assert output_volume.unpacked_value['id'] == '1'
        p_key_getter.assert_called_once_with(dummy_ready_volume.key)

    def test_volume_get_id_from_key_invalid_input(self):
        key = 'volumes'

        assert VolumeManager.get_id_from_key(key) == ''

    def test_volume_get_id_from_key(self):
        key = '/volumes/1'

        assert VolumeManager.get_id_from_key(key) == '1'
