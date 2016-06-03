from copy import deepcopy

from api import Volume
from tests.conftest import dummy_ready_volume


class TestVolume:
    def test_delete_cas(self, volume_manager, p_volume_manager_by_id, p_volume_manager_update, flask_app):
        volume = deepcopy(dummy_ready_volume)
        flask_app.volume_manager = volume_manager

        p_volume_manager_update.return_value = False
        p_volume_manager_by_id.return_value = volume

        with flask_app.app_context():
            result = Volume.delete('1')

            p_volume_manager_by_id.assert_called_with('1')
            assert result == ({'message': 'Resource changed during transition.'}, 409)

