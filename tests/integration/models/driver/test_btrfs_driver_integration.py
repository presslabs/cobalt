class TestBRTFSDriverIntegration:
    def test_create_volume(self, driver):
        assert driver.create({'id': '32', 'reserved_size': 1})
        assert '32' in driver.get_all()

    def test_remove_volume(self, driver):
        driver.create({'id': '32', 'reserved_size': 1})

        assert driver.remove('32')
        assert '32' not in driver.get_all()

    def test_clone_volume(self, driver):
        driver.create({'id': '32', 'reserved_size': 1})
        assert driver.clone('33', '32')
        assert '33' in driver.get_all()

    def test_get_usage(self, driver):
        assert driver.get_usage() == (4.0, [])

        driver.create({'id': '32', 'reserved_size': 2})
        assert driver.get_usage() == (4.0, [2.0])

    def test_resize_volume(self, driver):
        driver.create({'id': '32', 'reserved_size': 1})
        assert driver.get_usage() == (4.0, [1.0])

        driver.resize('32', 3)
        assert driver.get_usage() == (4.0, [3.0])

    def test_get_all(self, driver):
        for i in range(1, 4):
            driver.create({'id': i, 'reserved_size': 1})

        assert len(driver.get_all()) == 3
        assert '1' in driver.get_all()
        assert '2' in driver.get_all()
        assert '3' in driver.get_all()
