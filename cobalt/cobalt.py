import gevent

from engine.engine import Engine
from engine.lease import Lease
from utils.service import Service
from etcd import Client, Lock
from cobalt.config import context


class Cobalt(Service):

    def __init__(self):
        self.etcd = Client(**context['etcd'])

        engine_lock = Lock(self.etcd, 'leader-election')
        engine_leaser = Lease(engine_lock, **context['engine'])

        self.services = []

        service_map = {
            'engine': Engine(engine_leaser),
            # TODO add api / agent here
            # 'api', 'agent'
        }

        context_services = context['services'] if hasattr(context['services'], '__iter__') else [context['services']]
        for service in context_services:
            if service in service_map:
                self.services.append(service_map.get(service))

    def stop(self):
        for service in self.services:
            service.stop()

    def start(self):
        routines = []
        for service in self.services:
            routines += service.start()

        gevent.joinall(routines)
