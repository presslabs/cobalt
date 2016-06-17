# Copyright 2016 Presslabs SRL
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

import gevent
import time

from models.driver import BTRFSDriver
from models.manager import VolumeManager
from models.node import Node
from utils.service import Service


class Agent(Service):
    _interested_states = ['deleting', 'resizing', 'cloning', 'scheduling']

    def __init__(self, machine_manager, volume_manager, context):
        self._driver = BTRFSDriver(context['node']['volume_path'])
        self._from_etcd = None
        self._machine_manager = machine_manager
        self._volume_manager = volume_manager
        self._node = Node(context['node'], self._driver)
        self._work = []

        self._volume_loop = self._machine_loop = None
        self._max_error_count = context['max_error_count']
        self._error_timeout = context['max_error_timeout']
        self._delay = context['agent_ttl']
        self._watch_timeout = context['watch_timeout']
        self._started = False

    def start(self):
        if self._started:
            return []

        self._started = True
        self._volume_loop = gevent.spawn(self._run)
        self._machine_loop = gevent.spawn(self._machine_heartbeat)

        return [self._volume_loop, self._machine_loop]

    def stop(self):
        if not self._started:
            return False

        self._started = False

        return True

    @property
    def _quit(self):
        return not self._started

    def _run(self):
        self.reset()
        self._machine_heartbeat()

        while not self._quit:
            self._volume_heartbeat()
            self.timeout()

    def reset(self):
        self._from_etcd = self.get_all()

    def _machine_heartbeat(self):
        node = self._machine_manager.by_id(self._node.name)
        available, labels = self._node.get_space(), self._node.labels

        if node:
            node.value['available'] = available
            node.value['labels'] = labels
            self._machine_manager.update(node)
        else:
            node = dict(name=self._node.name, available=available, labels=labels)
            self._machine_manager.create(node, self._node.name)

    def _volume_heartbeat(self):
        self.reset()
        self.get_work()
        # Check for clutter first
        # (volumes that have been created but the task was reassigned
        #  in the meantime to another node)
        if len(self._node.get_subvolumes()) > len(self._from_etcd):
            self.do_cleanup()

        if len(self._work):
            self.do_work()
        else:
            volume = self._volume_manager.watch(timeout=self._watch_timeout)

            if volume:
                volume_conditions = (volume.value['node'] == self._node.name and
                                     volume.action not in ['expire', 'delete'] and
                                     volume.value['state'] in Agent._interested_states)

                if volume_conditions:
                    self._work.append(volume)
                    self.do_work()

    def timeout(self):
        time.sleep(self._delay)

    @staticmethod
    def _state_index(volume):
        state = volume.value['state']
        return Agent._interested_states.index(state) if state in Agent._interested_states else -1

    def get_all(self):
        return self._volume_manager.by_node(self._node.name)

    def get_work(self):
        self._work = [volume for volume in self._from_etcd if volume.value['state'] in Agent._interested_states]
        self._work = sorted(self._work, key=Agent._state_index)

    def do_create(self, volume_id, volume):
        success = False
        requirements = dict(id=volume_id, reserved_size=volume.value['requested']['reserved_size'])

        if self._driver.create(requirements):
            volume.value['node'] = self._node.name
            volume.value['actual'] = {
                'reserved_size': volume.value['requested']['reserved_size'],
                'constraints': volume.value['requested']['constraints']
            }
            volume.value['control']['error_count'] = 0
            volume.value['state'] = 'ready'
            success = True
        else:
            volume.value['control']['error_count'] += 1

        self._volume_manager.update(volume)
        return success

    def do_resize(self, volume_id, volume):
        success = False
        if self._driver.resize(volume_id, volume.value['requested']['reserved_size']):
            volume.value['actual']['reserved_size'] = volume.value['requested']['reserved_size']
            volume.value['state'] = 'pending'
            volume.value['control']['error_count'] = 0
            success = True
        else:
            volume.value['control']['error_count'] += 1

        self._volume_manager.update(volume)
        return success

    def do_clone(self, volume_id, volume):
        success = False
        if self._driver.clone(volume_id, volume.value['control']['parent_id']):
            volume.value['control']['parent_id'] = ''
            volume.value['control']['error_count'] = 0
            volume.value['state'] = 'ready'
            success = True
        else:
            volume.value['control']['error_count'] += 1

        self._volume_manager.update(volume)
        return success

    def do_delete(self, volume_id, volume=None):
        success = False

        if self._driver.remove(volume_id):
            success = True

        if not volume:
            return success

        if success:
            self._volume_manager.delete(volume)
        else:
            volume.value['control']['error_count'] += 1
            self._volume_manager.update(volume)

        return success

    def do_cleanup(self):
        for volume_id in self._node.get_subvolumes():
            if volume_id not in [self._volume_manager.get_id_from_key(volume.key) for volume in self._from_etcd]:
                self.do_delete(volume_id)

    def do_work(self):
        for volume in self._work:
            volume_id = self._volume_manager.get_id_from_key(volume.key)
            error_count = volume.value['control']['error_count']
            updated = volume.value['control']['updated']

            if (error_count and error_count % int(self._max_error_count) == 0 and
               time.time() - updated < self._error_timeout):
                continue
            else:
                success = False
                if volume.value['state'] == 'deleting':
                    success = self.do_delete(volume_id, volume)
                elif volume.value['state'] == 'resizing':
                    success = self.do_resize(volume_id, volume)
                elif volume.value['state'] == 'cloning':
                    success = self.do_clone(volume_id, volume)
                elif volume.value['state'] == 'scheduling':
                    success = self.do_create(volume_id, volume)

                if success:
                    self._machine_heartbeat()

            time.sleep(0)
