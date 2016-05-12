import time


class Lease(object):
    def __init__(self, lock, lease_ttl=60, refresh_ttl=40):
        self.lock = lock

        self.lease_ttl = 10 if lease_ttl < 10 else lease_ttl
        self.refresh_ttl = 6 if refresh_ttl < 6 else refresh_ttl

        if self.refresh_ttl >= self.lease_ttl:
            self.refresh_ttl = 2 * self.lease_ttl / 3

        self.quit = False

    def acquire(self):
        while not self.quit:
            self.lock.acquire(lock_ttl=self.lease_ttl, timeout=0)

            time.sleep(self.refresh_ttl)

    @property
    def is_held(self):
        return self.lock.is_acquired
