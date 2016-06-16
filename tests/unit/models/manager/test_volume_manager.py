# Copyright 2016 Presslabs SRL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from copy import deepcopy

from pytest import mark

from models.manager import VolumeManager
from tests.conftest import dummy_invalid_state_volume, dummy_ready_volume


class TestVolumeManager:
    def test_volume_manager_class_vars(self):
        assert VolumeManager.KEY == 'volumes'

    @mark.parametrize('query,filter,expected_result', [
        # all() return value, state to query, result
        ([], 'NONE', []),
        ([dummy_ready_volume], 'ready', [dummy_ready_volume]),
        ([dummy_ready_volume], 'readyish', []),
        ([], ['NONE'], []),
        ([dummy_ready_volume], ['ready'], [dummy_ready_volume]),
        ([dummy_invalid_state_volume], ['ready'], []),
        ([dummy_invalid_state_volume, dummy_ready_volume, dummy_invalid_state_volume], ['ready'], [dummy_ready_volume])
    ])
    def test_volume_by_states(self, query, filter, expected_result, volume_manager, p_volume_manager_all):
        p_volume_manager_all.return_value = (None, query)

        result = volume_manager.by_states(filter)

        assert expected_result == result
        assert p_volume_manager_all.called

    @mark.parametrize('volumes,filter,expected_result', [
        ([], 'NONE', []),
        ([dummy_ready_volume], 'ready', [dummy_ready_volume]),
        ([dummy_ready_volume], 'readyish', []),
        ([], ['NONE'], []),
        ([dummy_ready_volume], ['ready'], [dummy_ready_volume]),
        ([dummy_invalid_state_volume], ['ready'], []),
        ([dummy_invalid_state_volume, dummy_ready_volume, dummy_invalid_state_volume], ['ready'], [dummy_ready_volume])
    ])
    def test_volume_filter_states(self, volumes, filter, expected_result):
        result = VolumeManager.filter_states(volumes, filter)

        assert expected_result == result

    @mark.parametrize('parent_return', [False, dummy_ready_volume])
    def test_volume_update(self, mocker, parent_return, volume_manager):
        volume = deepcopy(dummy_ready_volume)
        parent_return = False if not parent_return else volume

        p_super_update = mocker.patch('models.manager.base_manager.BaseManager.update')
        p_super_update.return_value = parent_return

        output_volume = volume_manager.update(volume)

        if not parent_return:
            assert not output_volume
        else:
            assert output_volume

    def test_volume_create(self, mocker, volume_manager):
        data = {'control': {'update': None}}
        volume = deepcopy(dummy_invalid_state_volume)

        p_super_create = mocker.patch('models.manager.base_manager.BaseManager.create')
        p_super_create.return_value = volume

        output_volume = volume_manager.create(data)

        p_super_create.assert_called_with(data, '')
        assert output_volume

    def test_get_lock(self, volume_manager, m_etcd_client, p_etcd_lock):
        volume_manager.get_lock('1')

        p_etcd_lock.assert_called_with(m_etcd_client, 'clone-1')

    def test_get_lock_custom_purpose(self, volume_manager, m_etcd_client, p_etcd_lock):
        volume_manager.get_lock('1', 'foobar')

        p_etcd_lock.assert_called_with(m_etcd_client, 'foobar-1')

    def test_volume_get_id_from_key_invalid_input(self, mocker):
        key = 'volumes'

        assert VolumeManager(mocker.MagicMock()).get_id_from_key(key) == ''

    def test_volume_get_id_from_key(self, mocker):
        key = '/volumes/1'

        assert VolumeManager(mocker.MagicMock()).get_id_from_key(key) == '1'
