from copy import deepcopy
from utils import Service
from tests.conftest import dummy_ready_volume


class TestAgentUnit:
    def test_inherits_from_service(self, m_agent_service):
        assert isinstance(m_agent_service, Service)

    def test_start(self, mocker, m_agent_service, p_gevent_spawn):
        mocked_greenlet = mocker.MagicMock()
        p_gevent_spawn.return_value = mocked_greenlet

        assert m_agent_service.start() == [mocked_greenlet, mocked_greenlet]
        assert m_agent_service.stop()

    def test_already_started(self, mocker, m_agent_service, p_gevent_spawn):
        mocked_greenlet = mocker.MagicMock()
        p_gevent_spawn.return_value = mocked_greenlet

        m_agent_service.start()
        assert m_agent_service.start() == []
        m_agent_service.stop()

    def test_stop(self, m_agent_service):
        assert not m_agent_service.stop()

        m_agent_service.start()
        assert m_agent_service.stop()
        assert not m_agent_service.stop()

    def test_get_all(self, m_agent_service, volume_manager, p_volume_manager_by_node):
        volume = deepcopy(dummy_ready_volume)
        p_volume_manager_by_node.return_value = [volume]
        m_agent_service._volume_manager = volume_manager

        assert m_agent_service.get_all() == [volume]

    def test_get_work(self, m_agent_service):
        volume_ready = deepcopy(dummy_ready_volume)
        volume_scheduling = deepcopy(dummy_ready_volume)
        volume_scheduling.value['state'] = 'scheduling'

        m_agent_service._from_etcd = [volume_ready, volume_scheduling]
        m_agent_service.get_work()

        assert m_agent_service._work == [volume_scheduling]
