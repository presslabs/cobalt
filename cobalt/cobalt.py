import etcd
import gevent
import signal

from api import Api
from engine import Engine
from models import VolumeManager
from utils import Service
from config import config


class Cobalt(Service):
    def __init__(self):
        signal.signal(signal.SIGINT, self.handler)
        signal.signal(signal.SIGQUIT, self.handler)

        self.etcd = self._create_etcd(config['etcd'])
        self.volume_manager = self._create_volume_manager(self.etcd)
        self.config = config

        services = {
            'engine': Engine(self.etcd, self.volume_manager, self.config['engine']),
            'api': Api(self.volume_manager, self.config['api'])
            # TODO add api / agent here
            # 'api', 'agent'
        }

        self.services = {}

        context_services = self.config['services'] if isinstance(self.config['services'], list) else [self.config['services']]
        for service in context_services:
            if service in services:
                self.services[service] = services.get(service)

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

    @staticmethod
    def _create_etcd(context):
        return etcd.Client(**context)

    @staticmethod
    def _create_volume_manager(etcd):
        return VolumeManager(etcd)

    # TODO Unit test this

cobalt = Cobalt()
