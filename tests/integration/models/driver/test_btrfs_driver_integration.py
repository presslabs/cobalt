from models.driver.btrfsdriver import BTRFSDriver
import time


class TestBRTFSDriver:
    driver = BTRFSDriver('/mnt')

    def test_create_volume(self):
        assert TestBRTFSDriver.driver.create({'id': 32, 'reserved_size': 1})
        assert '32' in TestBRTFSDriver.driver.get_all()

    def test_remove_volume(self):
        assert TestBRTFSDriver.driver.remove('32')
        assert '32' not in TestBRTFSDriver.driver.get_all()

