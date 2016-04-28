import time

from etcd import Client, Lock
from gevent.monkey import patch_all
import gevent
import signal


class Engine(object):
    def __init__(self, lease_ttl=5, etcd_host='localhost'):
        self.lease_ttl = lease_ttl
        self.etcd = Client(host=etcd_host)
        self.lock = Lock(self.etcd, 'engine-lock')

    # TODO graceful exit
    def run(self):
        gevent.joinall([
            gevent.spawn(self.aquire_loop),
            gevent.spawn(self.schedule_loop),
        ])

        print('done')

    def aquire_loop(self):
        while True:
            print('aquire')
            self.lock.acquire(lock_ttl=self.lease_ttl)
            gevent.sleep(2 * self.lease_ttl / 3)

    def schedule_loop(self):
        while True:
            has_work = True
            print('schedule')
            if self.lock.is_acquired:
                # TODO May lose lock here: If task is long and network issues arise
                has_work = False
                pass
            else:
                print(self.lock.is_acquired)
                gevent.sleep(self.lease_ttl)

            if not has_work:
                gevent.sleep(self.lease_ttl)


def main():
    print('main')

    # gevent.signal(signal.SIGQUIT, gevent.kill)
    # patch_all()
    #
    # e = Engine()
    #
    # e.run()

    e = Client()
    l = Lock(e, 'engine-lock')

    l.acquire(lock_ttl=5)
    print(l.is_acquired)

    time.sleep(3)

    l.acquire(lock_ttl=5)
    print(l.is_acquired)

if __name__ == '__main__':
    main()