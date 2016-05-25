import gevent

from etcd import Client, Lock

from api import Api, app, register_resources, api_restful as api
from engine import Lease, Engine
from models import Volume
from utils import Service
from .config import context


class Cobalt(Service):

    def __init__(self):
        # TODO apply dependency injection here
        # TODO cleanup import paths
        self.etcd = Client(**context['etcd'])

        engine_lock = Lock(self.etcd, 'leader-election')
        engine_leaser = Lease(engine_lock, **context['engine'])
        engine_service = Engine(engine_leaser)

        app.volume_manager = Volume(self.etcd)
        register_resources(api)
        api_service = Api(app, (context['api']['host'], context['api']['port']))

        service_map = {
            'engine': engine_service,
            'api': api_service
            # TODO add api / agent here
            # 'api', 'agent'
        }

        self.services = []

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

    # TODO Unit test this
