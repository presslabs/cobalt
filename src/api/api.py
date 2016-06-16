# Copyright 2016 Presslabs SRL
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
    """ API service responsible for processing requests given by the client"""

    def __init__(self, volume_manager, context):
        """

        Args:
            volume_manager (VolumeManager): The repository object to work with the volumes
            context (dict): A dict containing `host` and `port`
        """
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
        """Responsible for spawning the coroutines that run the flask server

        Returns ([Greenlet]): A list of greenlets to join in the caller

        """
        if self._started:
            return []

        self._started = True
        self._api_loop = gevent.spawn(self._api_server.serve_forever)

        return [self._api_loop]

    def stop(self):
        """A means of stopping the service gracefully

        Returns (bool): Whether the code needed stopping or not

        """
        if not self._started:
            return False

        self._started = False
        self._api_server.stop()

        return True

    @staticmethod
    def _create_app(volume_manager, testing=False):
        """Factory method to create the Flask app and register all dependencies

        Args:
            volume_manager (VolumeManager): The volume manager to be used withing the API controller
            testing (bool): Whether or not to set the `TESTING` flag on the newly generated Flask application

        Returns (Flask): The application with all the needed dependencies bootstrapped

        """
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
        """Utility method to inject the resources and their endpoints

        Args:
            api (flask_restful.API): The API instance that needs to have the resources added.

        """
        api.add_resource(VolumeList, '/volumes')
        api.add_resource(Volume, '/volumes/<volume_id>')
