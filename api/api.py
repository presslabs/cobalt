import gevent

from gevent.pywsgi import WSGIServer
from flask import request_started

from utils.service import Service
from api.app import app


class Api(Service):
    def __init__(self, volume_manager, host='', port=5000):
        self._api_server = WSGIServer((host, port), app)
        app.volume_manager = volume_manager

        request_started.connect(Api._new_request, app)

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

    @staticmethod
    def _new_request(sender, **extra):
        sender.volume_manager.reset_cache()

