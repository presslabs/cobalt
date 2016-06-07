class TestDriver:
    def test_get_path(self, m_driver):
        id = 35
        expected = '/volumes/35'
        assert m_driver._get_path(id) == expected

    def test_get_quota(self, m_driver):
        quota = 3
        assert m_driver._get_quota(quota).endswith('G')

    def test_get_all(self, mocker, m_driver):
        btrfs = mocker.MagicMock()
        btrfs.return_value = """
            ID 356 gen 251 top level 258 path root/var/lib/machines
            ID 358 gen 282 top level 258 path root/snapshots/35
            ID 359 gen 294 top level 258 path root/snapshots/39
            ID 360 gen 277 top level 258 path root/snapshots/44
            ID 361 gen 278 top level 258 path root/snapshots/67
            ID 362 gen 279 top level 258 path root/snapshots/12
            ID 363 gen 341 top level 258 path root/volumes/55
        """
        m_driver._btrfs = btrfs

        assert m_driver.get_all() == [55]

    def test_df(self, mocker, m_driver):
        btrfs = mocker.MagicMock()
        btrfs.return_value = """
            Data, single: total=95.48GiB, used=5.21GiB
            System, DUP: total=0.01GiB, used=0.00GiB
            System, single: total=0.00GiB, used=0.00GiB
            Metadata, DUP: total=1.00GiB, used=0.06GiB
            Metadata, single: total=0.01GiB, used=0.00GiB
            GlobalReserve, single: total=0.03GiB, used=0.00GiB
        """
        m_driver._btrfs = btrfs

        assert m_driver.df() == (95.48, 5.21)
