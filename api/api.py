import gevent

from flask import Flask
from flask_restful import Api as RestApi
from gevent.pywsgi import WSGIServer

from utils import Service
from .volume import VolumeList, Volume


class Api(Service):
    def __init__(self, volume_manager, context):
        self._api_loop = None
        self._api_server = None
        self._started = False

        self._connection = ('', 5000)
        try:
            self._connection = (context['host'], int(context['port']))
        except (KeyError, ValueError) as e:
            print('Context provided to api erroneous: {}, defaulting: {}\n{}'.format(context, self._connection, e))

        self.flask_app = Api._create_app(volume_manager)
        self._api_server = WSGIServer(self._connection, self.flask_app)

    def start(self):
        if self._started:
            return []

        self._started = True
        self._api_loop = gevent.spawn(self._api_server.serve_forever)

        return [self._api_loop]

    def stop(self):
        if not self._started:
            return False

        self._started = False
        self._api_server.stop()

        return True

    @staticmethod
    def _create_app(volume_manager, testing=False):
        unhandled_exception_errors = {
            'EtcdConnectionFailed': {
                'message': "The ETCD cluster is not responding.",
                'status': 503,
            }
        }

        config = {
            'RESTFUL_JSON': {
                'separators': (', ', ': '),
                'indent': 2,
                'sort_keys': False
            },
            'TESTING': testing
        }

        app = Flask(__name__)
        app.config.update(**config)
        app.debug=True # todo remove this
        api = RestApi(app, errors=unhandled_exception_errors, catch_all_404s=True)
        Api._register_resources(api)

        app.volume_manager = volume_manager
        app.api = api

        return app

    @staticmethod
    def _register_resources(api):
        api.add_resource(VolumeList, '/volumes')
        api.add_resource(Volume, '/volumes/<volume_id>')
