import pytest

from pytest_mock import mock_module

from utils import Service
from engine import Engine


class TestEngine:
    def test_inherits_from_service(self, engine):
        assert isinstance(engine, Service)

    @pytest.mark.parametrize('method', ['start', 'stop'])
    def test_implements_from_service(self, method):
        assert Engine.__dict__.get(method)

    def test_start(self, mocker, engine, lease, gevent_spawn):
        mocked_greenlet = mocker.MagicMock()
        gevent_spawn.return_value = mocked_greenlet

        assert engine.start() == [mocked_greenlet, mocked_greenlet]
        assert not engine.start()

        call = mock_module.call
        gevent_spawn.assert_has_calls([call(lease.acquire), call(engine._run)], any_order=True)

        assert engine.stop()

    @pytest.mark.usefixtures('gevent_spawn')
    def test_stop(self, engine):
        assert not engine.stop()

        engine.start()

        assert engine.stop()
        assert engine._quit
        assert not engine.stop()

    @pytest.mark.parametrize('lease_held', [False, True])
    def test_run_with_lease(self, mocker, lease_held, engine, lease, executor):
        engine._started = True

        type(engine)._quit = mocker.PropertyMock(side_effect=[False, True])
        type(lease).is_held = mocker.PropertyMock(return_value=lease_held)

        engine._run()

        if lease_held:
            executor.tick.assert_called_once_with()
        executor.timeout.assert_called_once_with()
