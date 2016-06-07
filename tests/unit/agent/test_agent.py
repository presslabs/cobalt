from copy import deepcopy
from utils import Service
from tests.conftest import dummy_ready_volume


class TestAgent:
    def test_inherits_from_service(self, agent_service):
        assert isinstance(agent_service, Service)

    def test_start(self, mocker, agent_service, p_gevent_spawn):
        mocked_greenlet = mocker.MagicMock()
        p_gevent_spawn.return_value = mocked_greenlet

        assert agent_service.start() == [mocked_greenlet, mocked_greenlet]
        assert agent_service.stop()

    def test_stop(self, agent_service):
        assert not agent_service.stop()

        agent_service.start()
        assert agent_service.stop()
        assert not agent_service.stop()

    def test_get_all(self, agent_service, volume_manager, p_volume_manager_by_node):
        volume = deepcopy(dummy_ready_volume)
        p_volume_manager_by_node.return_value = [volume]
        agent_service._volume_manager = volume_manager

        assert agent_service.get_all() == [volume]

    def test_get_work(self, agent_service):
        volume_ready = deepcopy(dummy_ready_volume)
        volume_scheduling = deepcopy(dummy_ready_volume)
        volume_scheduling.value['state'] = 'scheduling'

        agent_service._from_etcd = [volume_ready, volume_scheduling]
        agent_service.get_work()

        assert agent_service._work == [volume_scheduling]
