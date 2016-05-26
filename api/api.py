import gevent

from flask import Flask
from gevent.pywsgi import WSGIServer
from werkzeug.debug import DebuggedApplication

from utils import Service, Connection


class Api(Service):
    def __init__(self, app: Flask, connection: Connection=Connection('', 5000)) -> None:
        self._api_server = WSGIServer(connection, app)

        self._api_loop = None
        self._started = False

    def start(self) -> [gevent.Greenlet]:
        if self._started:
            return []

        self._started = True
        self._api_loop = gevent.spawn(self._api_server.serve_forever)

        return [self._api_loop]

    def stop(self) -> bool:
        if not self._started:
            return False

        self._started = False
        self._api_server.stop()

        return True
