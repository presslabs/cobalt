# Copyright 2016 Presslabs SRL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time


class Lease(object):

    """Engine Lease acquisition class.

    It is responsible for watching the state of the Lock and refresh it so to maintain
    Leader status
    """

    def __init__(self, lock, context):
        """Create a Lease object.

        Args:
            lock (etcd.Lock): The lock it should monitor
            context (dict): The configuration for timeouts related to the Lease object
        """
        self.lock = lock

        self.lease_ttl = 10 if context['lease_ttl'] < 10 else context['lease_ttl']
        self.refresh_ttl = 6 if context['refresh_ttl'] < 6 else context['refresh_ttl']

        if self.refresh_ttl >= self.lease_ttl:
            self.refresh_ttl = 2 * self.lease_ttl / 3

        self.quit = False

    def acquire(self):
        """The acquisition loop that first acquires then refreshes it.

        When the Leaser quits it will automatically release the leader status so others may take action
        """
        while not self.quit:
            self.lock.acquire(lock_ttl=self.lease_ttl, timeout=0)

            time.sleep(self.refresh_ttl)

        self.lock.release()

    @property
    def is_held(self):
        """Helper property so to access the acquired state of the Lock easier."""
        return self.lock.is_acquired
