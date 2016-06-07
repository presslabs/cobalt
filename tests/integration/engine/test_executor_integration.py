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

import json
import threading
import time

from models.manager import VolumeManager


class TestExecutorIntegration:
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
        #assert test_volume.modifiedIndex != volume.createdIndex
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

        # these ticks should reset local state, the watch is failing
        # there are 2 because there were 2 updates before the watch started
        executor.tick()
        executor.tick()

        # this should move one volume to the other machine
        executor.tick()

        volumes = volume_manager.all()[1]
        for index, test_volume in enumerate(volumes):
            state = test_volume.value.pop('state')
            node = test_volume.value.pop('node')

            assert test_volume.modifiedIndex != test_volume.createdIndex
            assert state == 'scheduling'
            assert node == '{}'.format(index)

    def test_process_with_watch(self, executor, etcd_client, volume_manager):
        machine_data = ["""
            {
                "name": "0",
                "labels": [],
                "available": 1
            }
        """]

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
        self._create_entries('machines', machine_data, etcd_client)

        executor._should_reset = False
        executor.delay = 3

        def ticker():
            executor.tick()

        watch = threading.Thread(target=ticker)
        watch.start()

        time.sleep(0.1)

        created_volume = self._create_entries('volumes', volume_data, etcd_client)[0]
        created_volume.value = json.loads(created_volume.value)

        # discard data that we know changes to test them separately
        created_volume.value['control'].pop('updated')
        created_volume.value.pop('node')

        watch.join(5)
        if watch.is_alive():
            assert False, 'Operations still in progress, watcher timed out.'

        existing_volume = volume_manager.by_id(volume_manager.get_id_from_key(created_volume.key))
        updated = existing_volume.value['control'].pop('updated')
        node = existing_volume.value.pop('node')

        assert node == '0'
        assert updated != 0
        assert existing_volume.value == created_volume.value

        # no modifiedIndex + 1 here because this is already the modified volume,
        # it should be next in line again
        assert executor._watch_index == existing_volume.modifiedIndex

    def test_process_with_multiple_consecutive_watches(self, executor, etcd_client, volume_manager):
        machine_data = ["""
            {
                "name": "0",
                "labels": [],
                "available": 1
            }
        """]

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

        self._create_entries('machines', machine_data, etcd_client)

        executor._should_reset = False
        executor.delay = 3

        def ticker():
            executor.tick()
            executor.tick()

        watch = threading.Thread(target=ticker)
        watch.start()

        time.sleep(0.1)

        created_volumes = self._create_entries('volumes', volume_data, etcd_client)

        for created_volume in created_volumes:
            created_volume.value = json.loads(created_volume.value)

            # discard data that we know changes to test them separately
            created_volume.value['control'].pop('updated')
            created_volume.value.pop('node')

        watch.join(5)
        if watch.is_alive():
            assert False, 'Operations still in progress, watcher timed out.'

        existing_volumes = volume_manager.all()[1]

        assert len(existing_volumes) == len(created_volumes)

        # this is the modified index no need for +1, as this was not health checked by the watch
        assert executor._watch_index == existing_volumes[0].modifiedIndex

        for index, existing_volume in enumerate(existing_volumes):
            updated = existing_volume.value['control'].pop('updated')
            node = existing_volume.value.pop('node')

            assert node == '0'
            assert updated != 0
            assert existing_volume.value == created_volumes[index].value

    def test_process_with_multiple_watches_with_reset_between(self, executor, etcd_client, volume_manager):
        machine_data = ["""
            {
                "name": "0",
                "labels": [],
                "available": 1
            }
        """]

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

        self._create_entries('machines', machine_data, etcd_client)

        executor._should_reset = False
        executor.delay = 3

        def ticker():
            # watch
            executor.tick()

            # reset to pooling
            executor.reset()

            # pool both volumes
            executor.tick()
            executor.tick()

            # watch again
            executor.tick()

        watch = threading.Thread(target=ticker)
        watch.start()

        time.sleep(0.1)

        created_volumes = self._create_entries('volumes', volume_data, etcd_client)

        for created_volume in created_volumes:
            created_volume.value = json.loads(created_volume.value)

            # discard data that we know changes to test them separately
            created_volume.value['control'].pop('updated')
            created_volume.value.pop('node')

        watch.join(5)
        if watch.is_alive():
            assert False, 'Operations still in progress, watcher timed out.'

        existing_volumes = volume_manager.all()[1]

        assert len(existing_volumes) == len(created_volumes)
        assert executor._watch_index == existing_volumes[1].modifiedIndex + 1

        for index, existing_volume in enumerate(existing_volumes):
            updated = existing_volume.value['control'].pop('updated')
            node = existing_volume.value.pop('node')

            assert node == '0'
            assert updated != 0
            assert existing_volume.value == created_volumes[index].value

    def _create_entries(self, key, entry_data, etcd_client):
        entries = []
        for data in entry_data:
            entries.append(etcd_client.write(key, data, append=True))

        return entries
