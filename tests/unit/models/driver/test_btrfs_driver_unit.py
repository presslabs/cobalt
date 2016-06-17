class TestBTRFSDriverUnit:
    def test_get_path(self, m_driver):
        id = '35'
        expected = '/mnt/35'
        assert m_driver._get_path(id) == expected

    def test_get_quota(self, m_driver):
        quota = 3
        assert m_driver._get_quota(quota).endswith('G')

    def test_get_all(self, mocker, m_driver):
        btrfs = mocker.MagicMock()
        btrfs.return_value = """ID 356 gen 251 top level 258 path root/var/lib/machines
ID 358 gen 282 top level 258 path root/snapshots/35
ID 359 gen 294 top level 258 path root/snapshots/39
ID 360 gen 277 top level 258 path root/snapshots/44
ID 361 gen 278 top level 258 path root/snapshots/67
ID 362 gen 279 top level 258 path root/snapshots/12
ID 363 gen 341 top level 258 path root/mnt/55"""
        m_driver._btrfs = btrfs

        assert m_driver.get_all() == ['55']

    def test_get_usage(self, mocker, m_driver, s_btrfs_cmd_side_effect):
        btrfs = mocker.MagicMock(side_effect=s_btrfs_cmd_side_effect)

        m_driver._btrfs = btrfs

        get_all = mocker.MagicMock()
        get_all.return_value = ['12', '13', '14']
        m_driver.get_all = get_all

        assert m_driver.get_usage() == (97.51, [1.0, 1.0, 1.0])

