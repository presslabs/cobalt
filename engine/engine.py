import gevent
import time

from engine.lease import Lease
from utils.service import Service


class Engine(Service):

    # TODO see how to inject an etcd reader / writer
    def __init__(self, lease: Lease):
        self.lease = lease

        self._leaser_loop = None
        self._runner_loop = None

        self._started = False
        self.quit = False

    def start(self):
        if self._started:
            return

        self._started = True
        self.quit = False

        self._leaser_loop = gevent.spawn(self.lease.acquire)
        self._runner_loop = gevent.spawn(self._run)

        return [self._runner_loop, self._leaser_loop]

    def stop(self):
        if not self._started:
            return

        self.lease.quit = True
        self.quit = True
        self._started = False

    def _run(self):
        while not self.quit:
            if not self.lease.is_held:
                # TODO read from config
                time.sleep(10)
                continue

            # required for yield so other coroutines can function
            time.sleep(10)

    # http://stackoverflow.com/a/13602029