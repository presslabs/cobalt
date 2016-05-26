import pytest

from api import Api
from utils import Service


class TestApi:
    def test_inherits_from_service(self, api_service):
        assert isinstance(api_service, Service)

    @pytest.mark.parametrize('method', ['start', 'stop'])
    def test_implements_from_service(self, method):
        assert Api.__dict__.get(method)

    def test_start(self, mocker, api_service, api_server, gevent_spawn):
        mocked_greenlet = mocker.MagicMock()
        gevent_spawn.return_value = mocked_greenlet

        assert api_service.start() == [mocked_greenlet]
        assert not api_service.start()

        gevent_spawn.assert_called_once_with(api_server.serve_forever)

        assert api_service.stop()

    @pytest.mark.usefixtures('gevent_spawn')
    def test_stop(self, api_service, api_server):
        assert not api_service.stop()

        api_service.start()

        assert api_service.stop()
        assert not api_service.stop()
        api_server.stop.assert_called_once_with()
