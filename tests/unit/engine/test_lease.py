import pytest

from engine.lease import Lease


class TestLease:
    def test_initialization(self, mocker):
        lock = mocker.MagicMock(is_aquired=False)
        lease = Lease(lock, 9)

        assert lease.lock == lock
        assert not lease.is_held

    def test_acquire(self, mocker):
        lock = mocker.MagicMock()
        lock.acquire.side_effect = [True, RuntimeError]  # Exception here is to stop the infinite loop
        lock.release.side_effect = None

        # Mock the is_acquired property
        # as per https://docs.python.org/3/library/unittest.mock.html#unittest.mock.PropertyMock
        type(lock).is_acquired = mocker.PropertyMock(return_value=True)

        mocker.patch('engine.lease.time.sleep', return_value=None)

        lease = Lease(lock, 10)

        with pytest.raises(RuntimeError):
            lease.acquire()

        assert lease.is_held
