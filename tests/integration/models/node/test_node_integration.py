from os import path


class TestNodeIntegration:
    def test_get_subvolumes(self, driver, node):
        driver.create({'id': 32, 'reserved_size': 1})
        assert '32' in node.get_subvolumes()

    def test_get_space(self, driver, node):
        driver.create({'id': 32, 'reserved_size': 1})
        assert 2.2 == node.get_space()

    def test_conf_file_existence(self, node):
        assert path.isfile('/etc/cobalt.conf')
