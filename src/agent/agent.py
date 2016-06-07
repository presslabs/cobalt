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

import time

import gevent

from models.driver import BTRFSDriver
from models.node import Node
from utils.service import Service


class Agent(Service):
    def __init__(self, volume_manager, context):
        # Not sure if I need this anymore
        # self._from_node = None
        self._driver = BTRFSDriver(context['node']['volume_path'])
        self._from_etcd = None
        self._manager = volume_manager
        self._max_error_count = context['max_error_count']
        self._node = Node(context['node'])
        self._watch_timeout = context['watch_timeout']
        self._work = []

        self._agent_loop = None
        self._delay = context['agent_ttl']
        self._started = False

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
        pass


    def _volume_heartbeat(self):
        self.get_work()

        if len(self._work) > 0:
            self.do_work()
        else:
            volume = self._manager.watch(timeout=self._watch_timeout)
            if volume is not None and volume.value['node'] == self._node.name and volume.value['state'] != 'ready':
                self._work.append(volume)
                self.do_work()
            else:
                self.reset()

    def timeout(self):
        time.sleep(self._delay)

    def get_from_node(self):
        return self._node.get_subvolumes()

    def get_all(self):
        return self._manager.by_node(self._node.name)

    def get_work(self):
        self._work = [volume for volume in self._from_etcd if volume.value['state'] not in ['ready', 'pending']]

    def do_work(self):
        # Operation priority:
        #   deleting
        #   [moving]
        #   resizing
        #   cloning
        #   creating
        for volume in self._work:
            while time.time() - volume.value['control']['updated'] >= 10:
                id = self._manager.__class__.get_id_from_key(volume.key)

                if volume.value['state'] == 'deleting':
                    if self._driver.remove(id):
                        self._manager.delete(volume)
                    else:
                        volume.value['control']['error_count'] += 1
                        if volume.value['control']['error_count'] % self._max_error_count == 0:
                            volume.value['control']['updated'] = time.time()

                        self._manager.update(volume)
                elif volume.value['state'] == 'resizing':
                    if self._driver.resize(id, volume.value['requested']['reserved_size']):
                        volume.value['actual']['reserved_size'] = volume.value['requested']['reserved_size']
                        volume.value['state'] = 'pending'
                        volume.value['control']['error_count'] = 0
                        self._manager.update(volume)
                    else:
                        volume.value['control']['error_count'] += 1
                        if volume.value['control']['error_count'] % self._max_error_count == 0:
                            volume.value['control']['updated'] = time.time()

                        self._manager.update(volume)
                elif volume.value['state'] == 'cloning':
                    if self._driver.clone(volume.value['id'], volume.value['control']['parent_id']):
                        volume.value['control']['parent_id'] = ''
                        volume.value['control']['error_count'] = 0
                        self._manager.update(volume)
                    else:
                        volume.value['control']['error_count'] += 1
                        if volume.value['control']['error_count'] % self._max_error_count == 0:
                            volume.value['control']['updated'] = time.time()

                        self._manager.update(volume)
                elif volume.value['state'] == 'scheduling':
                    requirements = {
                        'id': id,
                        'reserved_size': volume.value['requested']['reserved_size']
                    }
                    if self._driver.create(requirements):
                        volume.value['actual'] = {
                            'node': self._node.name,
                            'reserved_size': volume.value['requested']['reserved_size']
                        }
                        volume.value['control']['error_count'] = 0
                        self._manager.update(volume)
                    else:
                        volume.value['control']['error_count'] += 1
                        if volume.value['control']['error_count'] % self._max_error_count == 0:
                            volume.value['control']['updated'] = time.time()

                        self._manager.update(volume)


