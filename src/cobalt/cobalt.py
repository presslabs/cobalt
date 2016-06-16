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

import signal

import etcd
import gevent
import time

from api import Api
from engine import Engine
from models.manager import VolumeManager, MachineManager
from utils import Service


class Cobalt(Service):
    """Main service class responsible for setting up and managing all Cobalt components"""

    VERSION = '0.1'
    """Version of the current Cobalt app, used to ensure consistency inside the cluster"""

    def __init__(self, config):
        """Creates an instance of the Cobalt class

        Args:
            config (dict): A config dict for each component
        """
        self.etcd = self._create_etcd(config['etcd'])
        self.volume_manager = self._create_volume_manager(self.etcd)
        self.machine_manager = self._create_machine_manager(self.etcd)
        self.config = config

        self._service_endpoints = {}
        self.services = {}

        self.setup_services()
        self.filter_services()
        self._attach_handlers()

    def setup_services(self):
        """A method to prepare the possible services that Cobalt can have"""

        self._service_endpoints = {
            'engine': Engine(self.etcd, self.volume_manager,
                             self.machine_manager, self.config['engine']),
            'api': Api(self.volume_manager, self.config['api'])
        }

    def filter_services(self):
        """It will only take the services present in the config given to Cobalt"""

        context_services = self.config['services'] if isinstance(
            self.config['services'], list) else [self.config['services']]
        for service in context_services:
            if service in self._service_endpoints:
                self.services[service] = self._service_endpoints.get(service)

    def stop(self):
        """A means to gracefully stop all services registered to Cobalt

        Returns:
             bool: Returns true in any occasion
        """
        for _, service in self.services.items():
            service.stop()

        return True

    def start(self):
        """Starts Cobalt only if the ETCD versions match with the defined one

        Returns:
             bool: If the start operation succeded or not
        """
        if not self._ensure_versions_match():
            return False

        routines = []
        for _, service in self.services.items():
            routines += service.start()

        gevent.joinall(routines)

    def _ensure_versions_match(self):
        """Makes sure the versions match (the defined one and one remote)

        If this is the first node it will write its version upstream

        Returns:
             bool: If the versions match or not
        """
        while True:
            try:
                etcd_version = self.etcd.read('version')
                if etcd_version.value == self.VERSION:
                    return True

                print('VERSION MISMATCH: local={}, cluster={}'.format(self.VERSION, etcd_version.value))
                return False
            except etcd.EtcdConnectionFailed:
                print('Connection not established with ETCD.')
                return False
            except etcd.EtcdKeyNotFound:
                etcd_version = self._write_version()

                if etcd_version == self.VERSION:
                    return True
            except etcd.EtcdException as e:
                print('Unhandled exception {}'.format(e))
                return False

            print('Cobalt cluster version not ensured, trying again in 1 sec.')
            time.sleep(1)

    def _write_version(self):
        """Utility method to write current version upstream

        Returns:
            bool: If the write operation was successful or not
        """
        try:
            update_version = self.etcd.write('version', self.VERSION,
                                             prevExists=False)

            return update_version.value
        except etcd.EtcdException:
            return False

    def _attach_handlers(self):
        """Utility method to ensure graceful stops when receiving termination signals"""
        signals = ['SIGHUP', 'SIGTERM', 'SIGINT', 'SIGQUIT']
        for sig in signals:
            code = getattr(signal, sig)
            signal.signal(code, self._handler)

    def _handler(self, signum, frame):
        """The handler that will execute when a signal is caught. Purpose: stopping the node"""
        print('Stopping...')
        self.stop()

    @staticmethod
    def _create_etcd(context):
        """Factory method for creating the etcd.Client to be used inside the app.

        Args:
            context (dict): The config for the client

        Returns:
             etcd.Client: Client to be used by the APP

        """
        return etcd.Client(**context)

    @staticmethod
    def _create_volume_manager(etcd):
        """Factory method for creating the VolumeManger to be used inside the app.

        Args:
            etcd (etcd.Client): The client responsible for communicating with the database

        Returns:
            VolumeManager: The volume manager to be used by the APP
        """
        return VolumeManager(etcd)

    @staticmethod
    def _create_machine_manager(etcd):
        """Factory method for creating the MachineManager to be used inside the app.

        Args:
            etcd (etcd.Client): The client responsible for communicating with the database

        Returns:
            MachineManager: The machine manager to be used by the APP

        """
        return MachineManager(etcd)
