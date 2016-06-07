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

import signal

import etcd
import gevent
from api import Api
from engine import Engine
from models.manager import VolumeManager, MachineManager
from utils import Service


class Cobalt(Service):
    def __init__(self, config):
        self.etcd = self._create_etcd(config['etcd'])
        self.volume_manager = self._create_volume_manager(self.etcd)
        self.machine_manager = self._create_machine_manager(self.etcd)
        self.config = config

        self._service_endpoints = {}
        self.services = {}

        self.setup_services()
        self.filter_services()
        self.attach_handlers()

    def setup_services(self):
        self._service_endpoints = {
            'engine': Engine(self.etcd, self.volume_manager,
                             self.machine_manager, self.config['engine']),
            'api': Api(self.volume_manager, self.config['api'])
            # TODO add api / agent here
            # 'api', 'agent'
        }

    def filter_services(self):
        context_services = self.config['services'] if isinstance(
            self.config['services'], list) else [self.config['services']]
        for service in context_services:
            if service in self._service_endpoints:
                self.services[service] = self._service_endpoints.get(service)

    def stop(self):
        for _, service in self.services.items():
            service.stop()

    def start(self):
        routines = []
        for _, service in self.services.items():
            routines += service.start()

        gevent.joinall(routines)

    def handler(self, signum, frame):
        print('Stopping..')
        self.stop()

    def attach_handlers(self):
        signal.signal(signal.SIGINT, self.handler)
        signal.signal(signal.SIGQUIT, self.handler)

    @staticmethod
    def _create_etcd(context):
        return etcd.Client(**context)

    @staticmethod
    def _create_volume_manager(etcd):
        return VolumeManager(etcd)

    @staticmethod
    def _create_machine_manager(etcd):
        return MachineManager(etcd)

