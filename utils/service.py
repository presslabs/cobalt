from gevent import Greenlet


class Service(object):
    def start(self) -> [Greenlet]:
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()
