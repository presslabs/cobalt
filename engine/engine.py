import gevent
import time

from engine.lease import Lease
from utils.service import Service


class Engine(Service):

    # TODO see how to inject an etcd reader / writer
    def __init__(self, lease: Lease):
        self.lease = lease

        self.leaser_loop = None
        self.runner_loop = None
        self.should_stop = False

        self._started = False
        self.quit = False

    def start(self):
        if self._started:
            return

        self.leaser_loop = gevent.spawn(self.lease.acquire)
        self.runner_loop = gevent.spawn(self._run)

        self._started = True
        return [self.runner_loop, self.leaser_loop]

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