from gevent.pywsgi import WSGIServer
from flask import Flask

from utils.service import Service
from api.volume import volume_blueprint


class Api(Service):

    # TODO: check and define the volume manager
    def __init__(self, host='', port=5000, volume_manager=None):
        self.volume_manager = volume_manager
        self.api_server = WSGIServer((host, port), self._create_api_server())

    def start(self):
        self.api_server.serve_forever()

        return []

    def stop(self):
        self.api_server.stop()

    def _create_api_server(self):
        app = Flask(__name__)
        app.register_blueprint(volume_blueprint, url_prefix='/volumes')
        app.volume_manager = self.volume_manager

        print(app.url_map)

        return app
