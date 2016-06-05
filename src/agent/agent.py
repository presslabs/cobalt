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

from time import time

import gevent

from models.driver import BTRFSDriver
from models.node import Node
from utils.service import Service


class Agent(Service):
    def __init__(self, machine_manager, volume_manager, context):
        self._driver = BTRFSDriver(context['node']['volume_path'])
        self._from_etcd = None
        self._machine_manager = machine_manager
        self._volume_manager = volume_manager
        self._node = Node(context['node'])
        self._work = []

        self._agent_loop = None
        self._max_error_count = context['max_error_count']
        self._delay = context['agent_ttl']
        self._watch_timeout = context['watch_timeout']
        self._started = False

        self._machine_heartbeat()

    def start(self):
        if self._started:
            return []

        self._started = True
        self._agent_loop = gevent.spawn(self._run)

        return [self._agent_loop]

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

        while not self._quit:
            self._machine_heartbeat()
            self._volume_heartbeat()
            self.timeout()

    def reset(self):
        self._from_etcd = self.get_all()

    def _machine_heartbeat(self):
        node = self._machine_manager.by_id(self._node.name)
        if node:
            node.value['available'] = self._node.get_space()
            node.value['labels'] = self._node.labels
        else:
            node = dict(id=self._node.name, available=self._node.get_space(), labels=self._node.labels)
        self._machine_manager.create(node, self._node.name)

    def _volume_heartbeat(self):
        self.get_work()

        if len(self._work) > 0:
            self.do_work()
        else:
            volume = self._volume_manager.watch(timeout=self._watch_timeout)
            if volume and volume.value['node'] == self._node.name and volume.value['state'] not in ['ready', 'pending']:
                self._work.append(volume)
                self.do_work()
            else:
                self.reset()

    def timeout(self):
        time.sleep(self._delay)

    def get_from_node(self):
        return self._node.get_subvolumes()

    def get_all(self):
        return self._volume_manager.by_node(self._node.name)

    def get_work(self):
        self._work = [volume for volume in self._from_etcd if volume.value['state'] not in ['ready', 'pending']]

    def do_work(self):
        for volume in self._work:
            while time() - volume.value['control']['updated'] >= 10:
                id = self._volume_manager.__class__.get_id_from_key(volume.key)

                if volume.value['state'] == 'deleting':
                    if self._driver.remove(id):
                        self._volume_manager.delete(volume)
                    else:
                        volume.value['control']['error_count'] += 1
                        if volume.value['control']['error_count'] % self._max_error_count == 0:
                            volume.value['control']['updated'] = time()

                        self._volume_manager.update(volume)
                elif volume.value['state'] == 'resizing':
                    if self._driver.resize(id, volume.value['requested']['reserved_size']):
                        volume.value['actual']['reserved_size'] = volume.value['requested']['reserved_size']
                        volume.value['state'] = 'pending'
                        volume.value['control']['error_count'] = 0
                        self._volume_manager.update(volume)
                    else:
                        volume.value['control']['error_count'] += 1
                        if volume.value['control']['error_count'] % self._max_error_count == 0:
                            volume.value['control']['updated'] = time()

                        self._volume_manager.update(volume)
                elif volume.value['state'] == 'cloning':
                    if self._driver.clone(volume.value['id'], volume.value['control']['parent_id']):
                        volume.value['control']['parent_id'] = ''
                        volume.value['control']['error_count'] = 0
                        self._volume_manager.update(volume)
                    else:
                        volume.value['control']['error_count'] += 1
                        if volume.value['control']['error_count'] % self._max_error_count == 0:
                            volume.value['control']['updated'] = time()

                        self._volume_manager.update(volume)
                elif volume.value['state'] == 'scheduling':
                    requirements = dict(id=id, reserved_size=volume.value['requested']['reserved_size'])

                    if self._driver.create(requirements):
                        volume.value['actual'] = {
                            'node': self._node.name,
                            'reserved_size': volume.value['requested']['reserved_size']
                        }
                        volume.value['control']['error_count'] = 0
                        self._volume_manager.update(volume)
                    else:
                        volume.value['control']['error_count'] += 1
                        if volume.value['control']['error_count'] % self._max_error_count == 0:
                            volume.value['control']['updated'] = time()

                        self._volume_manager.update(volume)

