from pytest import mark
from etcd import Lock

from pytest_mock import mock_module

from utils import Service
from engine import Engine, Lease, Executor


class TestEngine:
    def test_inherits_from_service(self, engine):
        assert isinstance(engine, Service)

    def test_start(self, mocker, engine, m_lease, p_gevent_spawn):
        mocked_greenlet = mocker.MagicMock()
        p_gevent_spawn.return_value = mocked_greenlet
        engine.lease = m_lease

        assert engine.start() == [mocked_greenlet, mocked_greenlet]
        assert not engine.start()

        call = mock_module.call
        p_gevent_spawn.assert_has_calls([call(m_lease.acquire), call(engine._run)], any_order=True)

        assert engine.stop()

    @mark.usefixtures('p_gevent_spawn')
    def test_stop(self, engine):
        assert not engine.stop()

        engine.start()

        assert engine.stop()
        assert engine._quit
        assert not engine.stop()

    @mark.parametrize('lease_held', [False, True])
    def test_run_with_lease(self, mocker, lease_held, engine, m_lease, m_executor):
        engine._started = True
        engine.lease = m_lease
        engine.executor = m_executor

        type(engine)._quit = mocker.PropertyMock(side_effect=[False, True])
        type(m_lease).is_held = mocker.PropertyMock(return_value=lease_held)

        engine._run()

        if lease_held:
            m_executor.tick.assert_called_once_with()
        else:
            m_executor.reset.assert_called_once_with()
        m_executor.timeout.assert_called_once_with()

    def test_create_lock(self, m_etcd_client):
        actual = Engine._create_lock(m_etcd_client)

        assert isinstance(actual, Lock)

    def test_create_leaser(self, m_lock):
        actual = Engine._create_leaser(m_lock, {'refresh_ttl': 10, 'lease_ttl': 9})

        assert isinstance(actual, Lease)

    def test_create_executor(self, m_volume_manager):
        actual = Engine._create_executor(m_volume_manager, {'timeout': 0})

        assert isinstance(actual, Executor)

