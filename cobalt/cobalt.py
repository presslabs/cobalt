import gevent

from etcd import Client, Lock
from werkzeug.debug import DebuggedApplication

from api import Api, app, register_resources, api_restful as api
from engine import Lease, Engine, Executor
from models import Volume
from utils import Service, Connection
from .config import context


class Cobalt(Service):

    def __init__(self):
        # TODO apply dependency injection here
        # TODO cleanup import paths
        self.etcd = Client(**context['etcd'])
        self.volume_manager = Volume(self.etcd)

        engine_lock = Lock(self.etcd, 'leader-election')
        engine_leaser = Lease(engine_lock, **context['engine'])
        executor = Executor(volume_manager=self.volume_manager, timeout=context['engine_executor']['timeout'])

        api_server_context = Connection(context['api']['host'], context['api']['port'])
        app.volume_manager = Volume(self.etcd)
        register_resources(api)

        _app = app
        if app.debug:
            _app = DebuggedApplication(app)

        service_map = {
            'engine': Engine(engine_leaser, executor),
            'api': Api(_app, api_server_context)
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
