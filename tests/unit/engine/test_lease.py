# Copyright 2016 PressLabs SRL
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

import pytest

from engine import Lease


class TestLease:
    def test_initialization(self, mocker):
        lock = mocker.MagicMock(is_acquired=False)
        lease = Lease(lock, {'lease_ttl': 10, 'refresh_ttl': 11})

        assert lease.lock == lock
        assert lease.lease_ttl == 10
        assert lease.refresh_ttl == 20 / 3
        assert not lease.is_held
        assert not lease.quit

    def test_acquire(self, mocker):
        lock = mocker.MagicMock()
        lock.acquire.side_effect = [True, RuntimeError]  # Exception here is to stop the infinite loop
        lock.release.side_effect = None

        type(lock).is_acquired = mocker.PropertyMock(return_value=True)

        mocker.patch('engine.lease.time.sleep', return_value=None)

        lease = Lease(lock, {'lease_ttl': 10, 'refresh_ttl': 6})

        with pytest.raises(RuntimeError):
            lease.acquire()

        assert lease.is_held

    def test_quit_acquire(self, mocker):
        lock = mocker.MagicMock(is_acquired=False)
        lease = Lease(lock, {'lease_ttl': 10, 'refresh_ttl': 11})

        lease.quit = True
        lease.acquire()

        assert not lock.acquire.called
        assert lock.release.called
        assert not lease.is_held
