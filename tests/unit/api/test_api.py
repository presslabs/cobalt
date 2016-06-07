# Copyright 2016 PressLabs SRL
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

from pytest import mark
from pytest_mock import mock_module

from utils import Service
from api import Api, Volume, VolumeList


class TestApi:
    def test_inherits_from_service(self, api_service):
        assert isinstance(api_service, Service)

    def test_start(self, mocker, api_service, p_api_server, p_gevent_spawn):
        mocked_greenlet = mocker.MagicMock()
        p_gevent_spawn.return_value = mocked_greenlet

        assert api_service.start() == [mocked_greenlet]
        assert not api_service.start()

        p_gevent_spawn.assert_called_once_with(p_api_server.serve_forever)

        assert api_service.stop()

    @mark.usefixtures('p_gevent_spawn', 'p_wsgi')
    def test_stop(self, api_service, p_api_server):
        assert not api_service.stop()

        api_service.start()

        assert api_service.stop()
        assert not api_service.stop()
        p_api_server.stop.assert_called_once_with()

    @mark.usefixtures('p_flask_restful')
    @mark.parametrize('testing', [True, False])
    def test_create_app(self, testing, volume_manager, m_flask_restful):
        app = Api._create_app(volume_manager, testing)

        assert app.config['TESTING'] == testing
        assert app.api == m_flask_restful
        assert app.volume_manager == volume_manager

    def test_register_resources(self, m_flask_restful):
        Api._register_resources(m_flask_restful)

        call = mock_module.call

        m_flask_restful.add_resource.assert_has_calls(
            [call(VolumeList, '/volumes'), call(Volume, '/volumes/<volume_id>')],
            any_order=True)
