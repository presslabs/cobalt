import gevent

from engine.lease import Lease
from utils.service import Service


class Engine(Service):

    # TODO see how to inject an etcd reader / writer
    def __init__(self, lease: Lease):
        self.lease = lease

        self.leaser_loop = None
        self.runner_loop = None
        self._started = False

    def start(self):
        if self._started:
            return

        self.leaser_loop = gevent.spawn(self.lease.acquire)
        self.runner_loop = gevent.spawn(self._run)

        gevent.joinall([self.runner_loop, self.leaser_loop], wait=0.0)
        self._started = True

    def stop(self):
        if not self._started:
            return

        gevent.killall([self.runner_loop, self.leaser_loop], block=False)
        self._started = False

    def _run(self):
        pass


    # http://stackoverflow.com/a/13602029