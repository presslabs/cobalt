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
from etcd import Lock

from utils import Service
from .executor import Executor
from .lease import Lease


class Engine(Service):
    def __init__(self, etcd, volume_manager, machine_manager, context):
        self.volume_manager = volume_manager
        self.machine_manager = machine_manager

        self.lease = self._create_leaser(self._create_lock(etcd), context['leaser'])
        self.executor = self._create_executor(self.volume_manager, self.machine_manager, context['executor'])

        self._leaser_loop = None
        self._runner_loop = None
        self._machine_loop = None

        self._started = False

    def start(self):
        if self._started:
            return []

        self._started = True

        self._leaser_loop = gevent.spawn(self.lease.acquire)
        self._runner_loop = gevent.spawn(self._run)
        self._machine_loop = gevent.spawn(self._machine_heartbeat)

        return [self._machine_loop, self._runner_loop, self._leaser_loop]

    def stop(self):
        if not self._started:
            return False

        self.lease.quit = True
        self._started = False

        return True

    @property
    def _quit(self):
        return not self._started

    def _run(self):
        while not self._quit:
            if not self.lease.is_held:
                self.executor.reset()
                self.executor.timeout()
                continue

            self.executor.tick()
            time.sleep(0)

    def _machine_heartbeat(self):
        machines = None

        while not self._quit:
            if not self.lease.is_held:
                self.executor.timeout()
                machines = None
                continue

            if machines is None:
                machines = self.machine_manager.all_keys()
                self.executor.timeout()
                continue

            new_machines = self.machine_manager.all_keys()
            if machines != new_machines:
                machines = new_machines
                self.executor.reset()

            self.executor.timeout()

    @staticmethod
    def _create_lock(etcd):
        return Lock(etcd, 'leader-election')

    @staticmethod
    def _create_executor(volume_manager, machine_manager, context):
        return Executor(volume_manager, machine_manager, context)

    @staticmethod
    def _create_leaser(lock, context):
        return Lease(lock, context)

