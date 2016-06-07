class TestNode:
    def test_name(self, m_node):
        assert m_node.name == 'test-node'

    def test_labels(self, m_node):
        assert len(m_node.labels) == 1
        assert m_node.labels == ['ssd']

    def test_get_space(self, mocker, m_driver, m_node):
        btrfs = mocker.MagicMock()
        m_driver._btrfs = btrfs
        m_node._driver = m_driver

        assert m_node.get_space() == 4.0