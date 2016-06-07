from copy import deepcopy

import etcd
from pytest import mark

from models.manager.base_manager import BaseManager
from tests.conftest import dummy_ready_volume


class TestBaseManager:
    def test_default_class_vars(self):
        assert BaseManager.KEY == ''

    def test_all_key_not_found(self, p_etcd_client_read, base_manager):
        p_etcd_client_read.side_effect = etcd.EtcdKeyNotFound

        dir, volumes = base_manager.all()

        assert dir is None
        assert volumes == []
        p_etcd_client_read.assert_called_with(BaseManager.KEY, sorted=True)

    def test_all_keys_except_the_dir(self, m_etcd_dir_result, p_etcd_client_read, p_base_manager_load_from_etcd,
                                     base_manager):
        dir_mock, entry_mock = m_etcd_dir_result

        # prepare result
        p_etcd_client_read.return_value = dir_mock
        p_base_manager_load_from_etcd.return_value = [entry_mock]

        # run
        _, volumes = base_manager.all()

        # make the needed assertions
        p_base_manager_load_from_etcd.assert_called_with([entry_mock])
        assert volumes == [entry_mock]
        p_etcd_client_read.assert_called_with(BaseManager.KEY, sorted=True)

    def test_all_keys(self, mocker, base_manager, p_base_manager_all):
        key = 1
        entry = mocker.MagicMock(key=key)
        p_base_manager_all.return_value = (None, [entry])

        keys = base_manager.all_keys()

        assert p_base_manager_all.called
        assert keys == [key]

    def test_all_keys_no_result(self, base_manager, p_base_manager_all):
        p_base_manager_all.return_value = (None, [])

        keys = base_manager.all_keys()

        assert p_base_manager_all.called
        assert keys == []

    def test_by_id_key_not_found(self, base_manager, p_etcd_client_read):
        p_etcd_client_read.side_effect = etcd.EtcdKeyNotFound

        volume = base_manager.by_id('1')

        assert volume is None
        p_etcd_client_read.assert_called_with('/{}/{}'.format(base_manager.KEY, '1'))

    def test_by_id(self, p_etcd_client_read, p_base_manager_load_from_etcd, base_manager, mocker):
        etcd_result_mock = mocker.MagicMock()
        p_etcd_client_read.side_effect = etcd_result_mock
        p_base_manager_load_from_etcd.return_value = etcd_result_mock

        volume = base_manager.by_id('1')

        assert volume == etcd_result_mock
        p_etcd_client_read.assert_called_with('/{}/{}'.format(BaseManager.KEY, '1'))

    @mark.parametrize('suffix', ['', 'suffix'])
    def test_volume_create(self, suffix, p_etcd_client_write, p_base_manager_load_from_etcd, p_json_dumps,
                           base_manager, mocker):
        p_json_dumps.return_value = '{}'
        etcd_result_mock = mocker.MagicMock(name='', value='{}')
        p_etcd_client_write.return_value = etcd_result_mock
        p_base_manager_load_from_etcd.return_value = etcd_result_mock

        result = base_manager.create({}, suffix=suffix)

        append = True if suffix == '' else False
        p_json_dumps.assert_called_with({})
        p_etcd_client_write.assert_called_with('/{}/{}'.format(BaseManager.KEY, suffix),
                                               '{}',
                                               append=append)

        p_base_manager_load_from_etcd.assert_called_with(etcd_result_mock)
        assert result == etcd_result_mock

    @mark.parametrize('error', [etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound])
    def test_volume_update_etcd_errors(self, p_etcd_client_update, p_json_dumps, base_manager, error):
        volume = deepcopy(dummy_ready_volume)
        p_json_dumps.return_value = {'name': 'test'}

        p_etcd_client_update.side_effect = error
        output_volume = base_manager.update(volume)

        assert not output_volume
        assert p_etcd_client_update.called

    def test_volume_update_etcd(self, p_etcd_client_update, base_manager, p_base_manager_load_from_etcd,
                                p_json_dumps):
        volume = deepcopy(dummy_ready_volume)

        p_json_dumps.return_value = {'name': 'test'}
        p_etcd_client_update.update.return_value = volume
        p_base_manager_load_from_etcd.return_value = volume

        output_volume = base_manager.update(volume)

        assert output_volume
        assert output_volume.value == volume.value
