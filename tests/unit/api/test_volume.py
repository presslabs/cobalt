from copy import deepcopy

from api import Volume
from tests.conftest import dummy_ready_volume


class TestVolume:
    def test_delete_case(self, mocker, volume_manager, p_volume_manager_by_id, p_volume_manager_update,
                        p_volume_manager_get_lock, flask_app):
        volume = deepcopy(dummy_ready_volume)
        flask_app.volume_manager = volume_manager

        p_volume_manager_update.return_value = False
        p_volume_manager_by_id.return_value = volume

        mocked_lock = mocker.MagicMock()
        mocked_lock.acquire.return_value = True
        mocked_lock.release.return_value = None
        p_volume_manager_get_lock.return_value = mocked_lock

        with flask_app.app_context():
            result = Volume.delete('1')

            p_volume_manager_by_id.assert_called_with('1')
            assert result == ({'message': 'Resource changed during transition.'}, 409)

        p_volume_manager_get_lock.assert_called_with('1', 'clone')

    def test_delete_pending_clones(self, mocker, volume_manager, p_volume_manager_by_id, p_volume_manager_all,
                                   p_volume_manager_update, p_volume_manager_get_lock, flask_app):
        parent_volume = deepcopy(dummy_ready_volume)
        clone_volume = deepcopy(dummy_ready_volume)
        clone_volume.value['control']['parent_id'] = '1'
        clone_volume.key = '/volumes/clone-1'

        flask_app.volume_manager = volume_manager

        p_volume_manager_update.return_value = False
        p_volume_manager_by_id.return_value = parent_volume
        p_volume_manager_all.return_value = (None, [parent_volume, clone_volume])

        mocked_lock = mocker.MagicMock()
        mocked_lock.acquire.return_value = True
        mocked_lock.release.return_value = None
        p_volume_manager_get_lock.return_value = mocked_lock

        with flask_app.app_context():
            result = Volume.delete('1')

            p_volume_manager_by_id.assert_called_with('1')
            assert result == ({'message': 'Resource has pending clones, can\'t delete.', 'clones': ['clone-1']}, 409)

        p_volume_manager_get_lock.assert_called_with('1', 'clone')
