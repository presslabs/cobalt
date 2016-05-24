from copy import deepcopy

from api.volume import Volume
from tests.conftest import dummy_ready_volume


class TestVolume:
    def test_delete_cas(self, mocker, unpacker, flask_app):
        volume_manager = mocker.MagicMock()
        flask_app.volume_manager = volume_manager

        volume = deepcopy(dummy_ready_volume)

        with flask_app.app_context():
            volume_manager.update.return_value = False
            volume_manager_by_id = mocker.patch.object(volume_manager, 'by_id')
            volume_manager_by_id.return_value = volume
            unpacker.return_value = [volume]

            result = Volume().delete('1')

            volume_manager_by_id.assert_called_with('1')
            assert result == ({'message': 'Resource changed during transition.'}, 409)
