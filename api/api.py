from gevent.pywsgi import WSGIServer
from flask import request_started

from utils.service import Service

from api.app import app


class Api(Service):
    def __init__(self, volume_manager, host='', port=5000):
        self.api_server = WSGIServer((host, port), app)
        app.volume_manager = volume_manager

        request_started.connect(Api._new_request, app)

    def start(self):
        self.api_server.serve_forever()

        return []

    def stop(self):
        self.api_server.stop()

    @staticmethod
    def _new_request(sender, **extra):
        sender.volume_manager.reset_cache()

