import json

from marshmallow import pprint

from models import VolumeManager


class TestExecutor:
    def test_scheduling_no_machines(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "scheduling",
                "node": "",
                "requested": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "actual": {},
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        volume = self._create_entries('volumes', volume_data, etcd_client)[0]

        executor.tick()

        test_volume = etcd_client.read(volume.key)

        assert test_volume.modifiedIndex == volume.createdIndex

    def test_scheduling_1_machine_labels_mismatch(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "scheduling",
                "node": "",
                "requested": {
                    "reserved_size": 1,
                    "constraints": ["ssd"]
                },
                "actual": {},
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        machine_data = ["""
            {
                "name": 1,
                "labels": [],
                "available": 200
            }
        """]

        volume = self._create_entries('volumes', volume_data, etcd_client)[0]
        self._create_entries('machines', machine_data, etcd_client)

        executor.tick()

        test_volume = etcd_client.read(volume.key)

        assert test_volume.modifiedIndex == volume.createdIndex

    def test_scheduling_1_machine_no_room(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "scheduling",
                "node": "",
                "requested": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "actual": {},
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        machine_data = ["""
            {
                "name": 1,
                "labels": [],
                "available": 0
            }
        """]

        volume = self._create_entries('volumes', volume_data, etcd_client)[0]
        self._create_entries('machines', machine_data, etcd_client)

        executor.tick()

        test_volume = etcd_client.read(volume.key)

        assert test_volume.modifiedIndex == volume.createdIndex

    def test_scheduling_2_machines_1_labels_mismatch_other_no_room(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "scheduling",
                "node": "",
                "requested": {
                    "reserved_size": 1,
                    "constraints": ["ssd"]
                },
                "actual": {},
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        machine_data = ["""
            {
                "name": 1,
                "labels": [],
                "available": 10
            }
        """, """
            {
                "name": 2,
                "labels": ["ssd"],
                "available": 0
            }
        """]

        volume = self._create_entries('volumes', volume_data, etcd_client)[0]
        self._create_entries('machines', machine_data, etcd_client)

        executor.tick()

        test_volume = etcd_client.read(volume.key)

        assert test_volume.modifiedIndex == volume.createdIndex

    def test_scheduling_2_machines_1_invalid_1_ok(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "scheduling",
                "node": "",
                "requested": {
                    "reserved_size": 1,
                    "constraints": ["ssd"]
                },
                "actual": {},
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        machine_data = ["""
            {
                "name": 1,
                "labels": [],
                "available": 10
            }
        """, """
            {
                "name": 2,
                "labels": ["ssd"],
                "available": 10
            }
        """]

        volume = self._create_entries('volumes', volume_data, etcd_client)[0]
        self._create_entries('machines', machine_data, etcd_client)

        executor.tick()

        test_volume = etcd_client.read(volume.key)

        test_volume_from_json = json.loads(test_volume.value)
        volume_from_json = json.loads(volume.value)

        volume_from_json.pop('node')
        assert test_volume.modifiedIndex != volume.createdIndex
        assert test_volume_from_json['control'].pop('updated') != volume_from_json['control'].pop('updated')
        assert test_volume_from_json.pop('node') == 2
        assert test_volume_from_json == volume_from_json

    def test_scheduling_2_machines_prioritize_largest(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "scheduling",
                "node": "",
                "requested": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "actual": {},
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        machine_data = ["""
            {
                "name": 1,
                "labels": ["ssd"],
                "available": 10
            }
        """, """
            {
                "name": 2,
                "labels": [],
                "available": 100
            }
        """]

        volume = self._create_entries('volumes', volume_data, etcd_client)[0]
        self._create_entries('machines', machine_data, etcd_client)

        executor.tick()

        test_volume = etcd_client.read(volume.key)

        test_volume_from_json = json.loads(test_volume.value)
        volume_from_json = json.loads(volume.value)

        volume_from_json.pop('node')
        assert test_volume.modifiedIndex != volume.createdIndex
        assert test_volume_from_json['control'].pop('updated') != volume_from_json['control'].pop('updated')
        assert test_volume_from_json.pop('node') == 2
        assert test_volume_from_json == volume_from_json

    def test_scheduling_machine_away_no_other_machine(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "scheduling",
                "node": "None",
                "requested": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "actual": {},
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        machine_data = ["""
            {
                "name": 1,
                "labels": ["ssd"],
                "available": 0
            }
        """, """
            {
                "name": 2,
                "labels": [],
                "available": 0
            }
        """]

        volume = self._create_entries('volumes', volume_data, etcd_client)[0]
        self._create_entries('machines', machine_data, etcd_client)

        executor.tick()

        test_volume = etcd_client.read(volume.key)

        assert test_volume.modifiedIndex == volume.createdIndex

    def test_scheduling_machine_away_1_other_available(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "scheduling",
                "node": "None",
                "requested": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "actual": {},
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        machine_data = ["""
            {
                "name": 1,
                "labels": [],
                "available": 10
            }
        """]

        volume = self._create_entries('volumes', volume_data, etcd_client)[0]
        self._create_entries('machines', machine_data, etcd_client)

        executor.tick()

        test_volume = etcd_client.read(volume.key)

        test_volume_from_json = json.loads(test_volume.value)
        volume_from_json = json.loads(volume.value)

        volume_from_json.pop('node')
        assert test_volume.modifiedIndex != volume.createdIndex
        assert test_volume_from_json['control'].pop('updated') != volume_from_json['control'].pop('updated')
        assert test_volume_from_json.pop('node') == 1
        assert test_volume_from_json == volume_from_json

    def test_not_interested_state(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "RANDOM",
                "node": "",
                "requested": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "actual": {},
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        machine_data = ["""
            {
                "name": 1,
                "labels": [],
                "available": 10
            }
        """]

        volume = self._create_entries('volumes', volume_data, etcd_client)[0]
        self._create_entries('machines', machine_data, etcd_client)

        executor.tick()

        test_volume = etcd_client.read(volume.key)

        assert test_volume.modifiedIndex == volume.createdIndex

    def test_no_volumes(self, executor):
        executor.delay = 0.1
        executor.tick()
        assert True

    def test_pending_no_changes(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "pending",
                "node": "",
                "requested": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "actual": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        volume = self._create_entries('volumes', volume_data, etcd_client)[0]

        executor.tick()

        test_volume = etcd_client.read(volume.key)

        test_volume_from_json = json.loads(test_volume.value)
        volume_from_json = json.loads(volume.value)

        test_volume_state = test_volume_from_json.pop('state')
        volume_from_json.pop('node')

        assert test_volume.modifiedIndex != volume.createdIndex
        assert test_volume_state != volume_from_json.pop('state')
        assert test_volume_state == 'ready'
        assert test_volume_from_json['control'].pop('updated') != volume_from_json['control'].pop('updated')
        assert test_volume_from_json.pop('node') == ''
        assert test_volume_from_json == volume_from_json

    def test_pending_to_cloning(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "RANDOM",
                "node": "1",
                "requested": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "actual": {},
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        machine_data = ["""
            {
                "name": "1",
                "labels": [],
                "available": 10
            }
        """]

        parent_volume = self._create_entries('volumes', volume_data, etcd_client)[0]
        self._create_entries('machines', machine_data, etcd_client)

        volume_data = json.loads(parent_volume.value)
        volume_data['state'] = 'pending'
        volume_data['control']['parent_id'] = VolumeManager.get_id_from_key(parent_volume.key)

        volume = self._create_entries('volumes', [json.dumps(volume_data)], etcd_client)[0]

        executor.tick()

        test_volume = etcd_client.read(volume.key)

        test_volume_from_json = json.loads(test_volume.value)
        volume_from_json = json.loads(volume.value)

        test_volume_state = test_volume_from_json.pop('state')
        volume_from_json.pop('node')

        assert test_volume.modifiedIndex != volume.createdIndex
        assert test_volume_state != volume_from_json.pop('state')
        assert test_volume_state == 'cloning'
        assert test_volume_from_json['control'].pop('updated') != volume_from_json['control'].pop('updated')
        assert test_volume_from_json.pop('node') == '1'

    def test_pending_to_cloning_missing_parent(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "pending",
                "node": "",
                "requested": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "actual": {},
                "control": {
                    "parent_id": "NONE",
                    "updated": 0
                }
            }
        """]

        volume = self._create_entries('volumes', volume_data, etcd_client)[0]

        executor.tick()

        test_volume = etcd_client.read(volume.key)

        test_volume_from_json = json.loads(test_volume.value)
        volume_from_json = json.loads(volume.value)

        volume_from_json.pop('node')
        assert test_volume.modifiedIndex != volume.createdIndex
        assert test_volume_from_json.pop('state') == 'deleting'
        assert test_volume_from_json['control'].pop('updated') != volume_from_json['control'].pop('updated')
        assert test_volume_from_json.pop('node') == ''

    def test_pending_to_resizing(self, executor, etcd_client):
        volume_data = ["""
            {
                "state": "pending",
                "node": "",
                "requested": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "actual": {
                    "reserved_size": 0,
                    "constraints": []
                },
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        volume = self._create_entries('volumes', volume_data, etcd_client)[0]

        executor.tick()

        test_volume = etcd_client.read(volume.key)
        test_volume_from_json = json.loads(test_volume.value)
        volume_from_json = json.loads(volume.value)

        volume_from_json.pop('node')
        assert test_volume.modifiedIndex != volume.createdIndex
        assert test_volume_from_json.pop('state') == 'resizing'
        assert test_volume_from_json['control'].pop('updated') != volume_from_json['control'].pop('updated')
        assert test_volume_from_json.pop('node') == ''

    def test_schedule_multiple_volumes_barely_enough_room(self, executor, etcd_client, volume_manager):
        volume_data = ["""
            {
                "state": "scheduling",
                "node": "",
                "requested": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "actual": {},
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """, """
            {
                "state": "scheduling",
                "node": "",
                "requested": {
                    "reserved_size": 1,
                    "constraints": []
                },
                "actual": {},
                "control": {
                    "parent_id": "",
                    "updated": 0
                }
            }
        """]

        machine_data = ["""
            {
                "name": "0",
                "labels": [],
                "available": 1
            }
        """, """
            {
                "name": "1",
                "labels": [],
                "available": 1
            }
        """]

        machines = self._create_entries('machines', machine_data, etcd_client)
        self._create_entries('volumes', volume_data, etcd_client)

        executor.delay = 0.1

        # process both volumes
        executor.tick()
        executor.tick()

        # emulate time passing by
        intermediate_volume = volume_manager.all()[1][1]
        intermediate_volume.value['control']['updated'] = 0.1
        data = json.dumps(intermediate_volume.value)
        etcd_client.write(intermediate_volume.key, data)

        # change state of machine as to simulate acceptance of a volume
        machine = machines[0]
        machine.value = json.loads(machine.value)
        machine.value['available'] = 0
        machine.value = json.dumps(machine.value)
        machines[0] = etcd_client.update(machine)

        # this tick should reset local state, the watch is failing
        executor.tick()

        # this should move one volume to the other machine
        executor.tick()

        volumes = volume_manager.all()[1]

        for index, test_volume in enumerate(volume_manager.all()[1]):
            test_volume_state = test_volume.value.pop('state')
            volumes[index].value.pop('node')
            volumes[index].value.pop('state')

            assert test_volume.modifiedIndex != volumes[index].createdIndex
            assert test_volume_state == 'scheduling'
            assert test_volume.value.pop('node') == '{}'.format(index)
            assert test_volume.value == volumes[index].value

    def test_process_with_watch_ignore_ttl_deleting(self, executor, etcd_client):
        pass

    def test_process_with_watch(self, executor, etcd_client):
        pass

    def test_process_with_multiple_consecutive_watches(self, executor, etcd_client):
        pass

    def test_process_with_multiple_watches_with_reset_between(self, executor, etcd_client):
        pass

    def _create_entries(self, key, entry_data, etcd_client):
        entries = []
        for data in entry_data:
            entries.append(etcd_client.write(key, data, append=True))

        return entries
