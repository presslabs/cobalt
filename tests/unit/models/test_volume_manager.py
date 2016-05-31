from copy import deepcopy

from flask import json
from pytest import mark

from models import VolumeManager
from tests.conftest import dummy_invalid_state_volume, dummy_ready_volume


class TestVolumeManager:
    def test_volume_manager_class_vars(self):
        assert VolumeManager.KEY == 'volumes'

    @mark.parametrize('query,state_filter,result', [
        # all() return value, state to query, result
        ([], 'NONE', []),
        ([dummy_invalid_state_volume], 'ready', []),
        ([dummy_invalid_state_volume, dummy_ready_volume, dummy_invalid_state_volume], 'ready', [dummy_ready_volume])
    ])
    def test_volume_by_state(self, query, state_filter, result, volume_manager, p_volume_manager_all):
        p_volume_manager_all.return_value = (None, query)

        volumes = volume_manager.by_state(state_filter)

        assert volumes == result
        assert p_volume_manager_all.called

    @mark.parametrize('parent_return', [False, dummy_ready_volume])
    def test_volume_update(self, mocker, parent_return, volume_manager, p_key_getter):
        volume = deepcopy(dummy_ready_volume)
        parent_return = False if not parent_return else volume

        p_super_update = mocker.patch('models.base_manager.BaseManager.update')
        p_super_update.return_value = parent_return
        p_key_getter.return_value = '1'

        output_volume = volume_manager.update(volume)

        if not parent_return:
            assert not output_volume
        else:
            assert output_volume
            assert output_volume.value['id'] == '1'
            p_key_getter.assert_called_once_with(volume.key)

    def test_volume_create(self, mocker, volume_manager, p_key_getter):
        data = {}
        volume = deepcopy(dummy_invalid_state_volume)

        p_super_create = mocker.patch('models.base_manager.BaseManager.create')
        p_super_create.return_value = volume
        p_key_getter.return_value = '1'

        output_volume = volume_manager.create(data)

        assert output_volume
        assert output_volume.value['id'] == '1'
        p_key_getter.assert_called_once_with(volume.key)

        p_super_create.assert_called_with(data, '')

    def test_volume_get_id_from_key_invalid_input(self):
        key = 'volumes'

        assert VolumeManager.get_id_from_key(key) == ''

    def test_volume_get_id_from_key(self):
        key = '/volumes/1'

        assert VolumeManager.get_id_from_key(key) == '1'
