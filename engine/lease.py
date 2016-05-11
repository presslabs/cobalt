import time


class Lease(object):
    def __init__(self, lock, lease_ttl=10):
        self.lock = lock
        self.lock.release()

        self.lease_ttl = 10 if lease_ttl < 10 else lease_ttl

    def acquire(self):
        while True:
            self.lock.acquire(lock_ttl=self.lease_ttl)

            time.sleep(self.lease_ttl * 2 / 3)

    @property
    def is_held(self):
        return self.lock.is_aquired
