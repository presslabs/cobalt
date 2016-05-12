from gevent import monkey
monkey.patch_all()

import signal

from cobalt.cobalt import Cobalt


cobalt = Cobalt()


def handler(signum, frame):
    print('Stopping..')
    cobalt.stop()

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGQUIT, handler)

cobalt.start()
