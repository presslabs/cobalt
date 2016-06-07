# Copyright 2016 PressLabs SRL
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

        api = RestApi(app, errors=unhandled_exception_errors, catch_all_404s=True)
        Api._register_resources(api)

        app.volume_manager = volume_manager
        app.api = api

        return app

    @staticmethod
    def _register_resources(api):
        api.add_resource(VolumeList, '/volumes')
        api.add_resource(Volume, '/volumes/<volume_id>')
