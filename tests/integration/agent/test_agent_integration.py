import json
import threading
import time

from models.manager import VolumeManager


class TestAgentIntegration:
    def test_reset(self, agent, etcd_client, volume_raw_ready_assigned):
        etcd_client.write(VolumeManager.KEY, volume_raw_ready_assigned, append=True)
        agent.reset()

        assert len(agent._from_etcd) == 1

        # JSON string needs to be reformatted before comparison
        volume_raw_ready_assigned = json.dumps(json.loads(volume_raw_ready_assigned))
        assert json.dumps(agent._from_etcd[0].value) == volume_raw_ready_assigned

    def test_machine_heartbeat_not_on_etcd(self, agent, machine_manager):
        assert machine_manager.by_id('test-node') is None
        agent._machine_heartbeat()

        node = machine_manager.by_id('test-node')

        assert node
        assert node.value['name'] == agent._node.name
        assert node.value['available'] == agent._node.get_space()
        assert node.value['labels'] == agent._node.labels

    def test_machine_heartbeat_on_etcd_value_changed(self, agent, machine_manager, mocker):
        machine_manager.create({'name': 'test-node', 'available': 4.0, 'labels': ['ssd']}, 'test-node')

        get_space = mocker.MagicMock()
        get_space.return_value = 3.0
        agent._node.get_space = get_space

        agent._machine_heartbeat()
        node = machine_manager.by_id('test-node')
        assert node.value['available'] == 3.0

    def test_volume_heartbeat_no_work_need_cleanup(self, agent, driver, volume_manager, volume_raw_ready_assigned):
        volume_manager.create(json.loads(volume_raw_ready_assigned))
        volume_manager.create(json.loads(volume_raw_ready_assigned))

        volumes = volume_manager.by_node('test-node')
        for volume in volumes:
            vol_id = volume_manager.get_id_from_key(volume.key)
            size = volume.value['requested']['reserved_size']
            driver.create({'id': vol_id, 'reserved_size': size})

        # Simulate volume that has been created by agent and
        # reassigned by engine in the meantime
        driver.create({'id': '666', 'reserved_size': 1})

        assert len(driver.get_all()) == 3
        assert '666' in driver.get_all()

        agent._volume_heartbeat()

        assert len(driver.get_all()) == 2
        assert '666' not in driver.get_all()

    def test_volume_heartbeat_no_cleanup_need_work(self, agent, driver, volume_manager, volume_raw_scheduling_assigned):
        volume_manager.create(json.loads(volume_raw_scheduling_assigned))
        volume_manager.create(json.loads(volume_raw_scheduling_assigned))
        volumes = volume_manager.by_node('test-node')

        assert len(volumes) == 2
        assert len(driver.get_all()) == 0

        agent._volume_heartbeat()

        assert len(driver.get_all()) == 2

    def test_volume_heartbeat_watch(self, agent, driver, volume_manager, volume_raw_scheduling_assigned):
        def volume_creator(volume):
            time.sleep(2)
            volume_manager.create(volume)

        volume = json.loads(volume_raw_scheduling_assigned)
        create_runner = threading.Thread(target=volume_creator, args=[volume])
        create_runner.start()
        agent._volume_heartbeat()

        assert len(driver.get_all()) == 1

    def test_do_create_success(self, agent, driver, volume_manager, volume_raw_scheduling_assigned):
        volume = json.loads(volume_raw_scheduling_assigned)
        volume_manager.create(volume)

        agent._volume_heartbeat()

        volume = volume_manager.by_node('test-node')[0]
        assert volume.value['state'] == 'ready'
        assert volume_manager.get_id_from_key(volume.key) == driver.get_all()[0]

    def test_do_create_failure(self, agent, volume_manager, volume_raw_scheduling_assigned):
        volume = json.loads(volume_raw_scheduling_assigned)
        volume['requested']['reserved_size'] = 'not_a_number'
        volume_manager.create(volume)

        agent._volume_heartbeat()

        volume = volume_manager.by_node('test-node')[0]
        assert volume.value['state'] == 'scheduling'
        assert volume.value['control']['error_count'] == 1

    def test_do_resize_success(self, agent, node, driver, volume_manager, volume_raw_scheduling_assigned):
        volume_create = json.loads(volume_raw_scheduling_assigned)

        volume_manager.create(volume_create)
        agent._volume_heartbeat()

        assert len(driver.get_all()) == 1
        assert node.get_space() == 2.2

        volume_resize = volume_manager.by_node('test-node')[0]
        volume_resize.value['state'] = 'resizing'
        volume_resize.value['requested']['reserved_size'] = volume_resize.value['actual']['reserved_size'] + 1
        volume_manager.update(volume_resize)

        agent._volume_heartbeat()

        volume = volume_manager.by_node('test-node')[0]
        assert volume.value['state'] == 'pending'
        assert volume.value['requested']['reserved_size'] == volume.value['actual']['reserved_size']
        assert node.get_space() == 1.2

    def test_do_resize_failure(self, agent, driver, node, volume_manager, volume_raw_scheduling_assigned):
        volume_create = json.loads(volume_raw_scheduling_assigned)
        volume_manager.create(volume_create)

        agent._volume_heartbeat()

        volume_resize = volume_manager.by_node('test-node')[0]
        volume_resize.value['state'] = 'resizing'
        volume_resize.value['requested']['reserved_size'] = 'not_a_number'
        volume_manager.update(volume_resize)

        agent._volume_heartbeat()

        print(driver.get_all())
        print(volume_manager.by_node('test-node'))

        volume_resize = volume_manager.by_node('test-node')[0]

        assert volume_resize.value['state'] == 'resizing'
        assert volume_resize.value['control']['error_count'] == 1
        assert len(driver.get_all()) == 1
        assert node.get_space() == 2.2

    def test_do_clone_success(self, agent, driver, volume_manager,
                              volume_raw_scheduling_assigned, volume_raw_cloning_assigned):
        volume = json.loads(volume_raw_scheduling_assigned)
        volume_manager.create(volume)

        agent._volume_heartbeat()

        volume = volume_manager.by_node('test-node')[0]
        parent_id = volume_manager.get_id_from_key(volume.key)

        volume = json.loads(volume_raw_cloning_assigned)
        volume['control']['parent_id'] = parent_id
        volume_manager.create(volume)

        agent._volume_heartbeat()
        volumes = volume_manager.by_node('test-node')

        assert len(driver.get_all()) == len(volumes) == 2
        assert volume_manager.get_id_from_key(volumes[0].key) in driver.get_all()
        assert volume_manager.get_id_from_key(volumes[1].key) in driver.get_all()

    def test_do_clone_failure(self, agent, driver, volume_manager,
                              volume_raw_scheduling_assigned, volume_raw_cloning_assigned):
        volume = json.loads(volume_raw_scheduling_assigned)
        volume_manager.create(volume)

        agent._volume_heartbeat()

        volume = json.loads(volume_raw_cloning_assigned)
        volume['control']['parent_id'] = 'invalid_id'
        volume_manager.create(volume)

        agent._volume_heartbeat()

        for volume in volume_manager.by_node('test-node'):
            if volume.value['control']['parent_id'] == 'invalid_id':
                assert volume.value['control']['error_count'] == 1
                assert volume.value['state'] == 'cloning'

        assert len(driver.get_all()) == 1

    def test_do_delete_success(self, agent, driver, volume_manager, volume_raw_scheduling_assigned):
        volume_create = json.loads(volume_raw_scheduling_assigned)
        volume_manager.create(volume_create)

        agent._volume_heartbeat()

        volume_delete = volume_manager.by_node('test-node')[0]
        volume_delete.value['state'] = 'deleting'
        volume_manager.update(volume_delete)

        agent._volume_heartbeat()

        assert len(driver.get_all()) == 0
        assert len(volume_manager.by_node('test-node')) == 0

    def test_do_delete_failure(self, agent, driver, volume_manager, volume_raw_scheduling_assigned):
        volume_create = json.loads(volume_raw_scheduling_assigned)
        volume_manager.create(volume_create)

        agent._volume_heartbeat()

        volume = volume_manager.by_node('test-node')[0]
        driver.remove(volume_manager.get_id_from_key(volume.key))

        volume.value['state'] = 'deleting'
        volume_manager.update(volume)

        agent._volume_heartbeat()

        volume_failed = volume_manager.by_node('test-node')[0]

        assert volume_failed.value['control']['error_count'] == 1
        assert volume_failed.value['state'] == 'deleting'
