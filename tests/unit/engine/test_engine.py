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

from etcd import Lock
from pytest import mark
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

        assert engine.start() == [mocked_greenlet, mocked_greenlet, mocked_greenlet]
        assert not engine.start()

        call = mock_module.call
        p_gevent_spawn.assert_has_calls([call(m_lease.acquire), call(engine._run), call(engine._machine_heartbeat)],
                                        any_order=True)

        assert engine.stop()

    @mark.usefixtures('p_gevent_spawn')
    def test_stop(self, engine):
        assert not engine.stop()

        engine.start()

        assert engine.stop()
        assert engine._quit
        assert not engine.stop()

    @mark.parametrize('lease_held', [False, True])
    def test_run_with_lease(self, mocker, p_time_sleep, lease_held, engine, m_lease, m_executor):
        engine._started = True
        engine.lease = m_lease
        engine.executor = m_executor

        type(engine)._quit = mocker.PropertyMock(side_effect=[False, True])
        type(m_lease).is_held = mocker.PropertyMock(return_value=lease_held)

        engine._run()

        if lease_held:
            m_executor.tick.assert_called_once_with()
            p_time_sleep.assert_called_once_with(0)
        else:
            m_executor.timeout.assert_called_once_with()
            m_executor.reset.assert_called_once_with()

    def test_machine_heartbeat_quit(self, engine, mocker):
        type(engine)._quit = mocker.PropertyMock(return_value=True)
        timeout = mocker.patch.object(engine.executor, 'timeout')
        reset = mocker.patch.object(engine.executor, 'reset')

        engine._machine_heartbeat()

        assert not timeout.called
        assert not reset.called

    @mark.usefixtures('p_engine_executor_timeout', 'p_engine_executor_reset')
    def test_machine_heartbeat_no_lease(self, engine, mocker, m_lease):
        engine.lease = m_lease
        type(m_lease).is_held = mocker.PropertyMock(return_value=False)
        type(engine)._quit = mocker.PropertyMock(side_effect=[False, True])

        engine._machine_heartbeat()

        executor = engine.executor

        executor.timeout.assert_called_once_with()
        assert not executor.reset.called

    @mark.usefixtures('p_engine_executor_timeout', 'p_engine_executor_reset')
    def test_machine_heartbeat_with_lease_once(self, engine, mocker, m_lease, p_machine_manager_all_keys):
        engine.lease = m_lease
        type(m_lease).is_held = mocker.PropertyMock(return_value=True)
        type(engine)._quit = mocker.PropertyMock(side_effect=[False, True])

        p_machine_manager_all_keys.return_value = ['1', '2']

        executor = engine.executor
        engine._machine_heartbeat()

        executor.timeout.assert_called_once_with()
        assert p_machine_manager_all_keys.called
        assert not executor.reset.called

    @mark.usefixtures('p_engine_executor_timeout', 'p_engine_executor_reset')
    def test_machine_heartbeat_with_lease_twice_no_change(self, engine, mocker, m_lease,
                                                          p_machine_manager_all_keys):
        engine.lease = m_lease
        type(m_lease).is_held = mocker.PropertyMock(return_value=True)
        type(engine)._quit = mocker.PropertyMock(side_effect=[False, False, True])

        p_machine_manager_all_keys.return_value = ['1', '2']

        executor = engine.executor
        engine._machine_heartbeat()

        call = mock_module.call
        executor.timeout.has_calls([call(), call()])
        p_machine_manager_all_keys.has_calls([call(), call()])

        assert not executor.reset.called

    @mark.usefixtures('p_engine_executor_timeout', 'p_engine_executor_reset')
    def test_machine_heartbeat_with_lease_twice_with_change(self, engine, mocker, m_lease,
                                                            p_machine_manager_all_keys):
        engine.lease = m_lease
        type(m_lease).is_held = mocker.PropertyMock(return_value=True)
        type(engine)._quit = mocker.PropertyMock(side_effect=[False, False, True])

        p_machine_manager_all_keys.side_effect = [['1', '2'], []]

        executor = engine.executor
        engine._machine_heartbeat()

        call = mock_module.call
        executor.timeout.has_calls([call(), call()])
        p_machine_manager_all_keys.has_calls([call(), call()])

        assert executor.reset.called

    @mark.usefixtures('p_engine_executor_timeout', 'p_engine_executor_reset')
    def test_machine_heartbeat_with_lease_thrice_no_change(self, engine, mocker, m_lease,
                                                           p_machine_manager_all_keys):
        engine.lease = m_lease
        type(m_lease).is_held = mocker.PropertyMock(return_value=True)
        type(engine)._quit = mocker.PropertyMock(side_effect=[False, False, False, True])

        p_machine_manager_all_keys.side_effect = [['1', '2'], [], []]

        executor = engine.executor
        engine._machine_heartbeat()

        call = mock_module.call
        executor.timeout.has_calls([call(), call(), call()])
        p_machine_manager_all_keys.has_calls([call(), call(), call()])
        executor.reset.assert_called_once_with()

    def test_create_lock(self, m_etcd_client):
        actual = Engine._create_lock(m_etcd_client)

        assert isinstance(actual, Lock)

    def test_create_leaser(self, m_lock):
        actual = Engine._create_leaser(m_lock, {'refresh_ttl': 10, 'lease_ttl': 9})

        assert isinstance(actual, Lease)

    def test_create_executor(self, volume_manager, machine_manager):
        actual = Engine._create_executor(volume_manager, machine_manager, {'timeout': 0})

        assert isinstance(actual, Executor)
