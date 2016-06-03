import time


class Lease(object):
    def __init__(self, lock, context):
        self.lock = lock

        self.lease_ttl = 10 if context['lease_ttl'] < 10 else context['lease_ttl']
        self.refresh_ttl = 6 if context['refresh_ttl'] < 6 else context['refresh_ttl']

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
