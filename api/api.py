import gevent

from gevent.pywsgi import WSGIServer
from werkzeug.debug import DebuggedApplication

from utils.service import Service
from api.app import app, api
from api.volume import register_resources


class Api(Service):
    def __init__(self, volume_manager, host='', port=5000):
        self._api_server = WSGIServer((host, port), DebuggedApplication(app))
        app.volume_manager = volume_manager
        register_resources(api)

        self._api_loop = None
        self._started = False

    def start(self):
        if self._started:
            return

        self._started = True
        self._api_loop = gevent.spawn(self._api_server.serve_forever)

        return [self._api_loop]

    def stop(self):
        if not self._started:
            return

        self._started = False
        self._api_server.stop()
