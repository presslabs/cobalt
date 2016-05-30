import etcd

from pytest import mark
from pytest_mock import mock_module

from models.base_manager import BaseManager, base_schema
from tests.conftest import dummy_ready_volume


class TestBaseManager:
    def test_default_class_vars(self):
        assert BaseManager.KEY == ''
        assert BaseManager.SCHEMA == base_schema

    def test_all_key_not_found(self, p_etcd_client_read, base_manager):
        p_etcd_client_read.side_effect = etcd.EtcdKeyNotFound

        volumes = base_manager.all()

        assert volumes == []
        p_etcd_client_read.assert_called_with(BaseManager.KEY, sorted=True)

    def test_all_keys_except_the_dir(self, m_etcd_dir_result, p_etcd_client_read, p_base_manager_unpacker,
                                     base_manager):
        dir_mock, entry_mock = m_etcd_dir_result

        # prepare result
        p_etcd_client_read.return_value = dir_mock
        p_base_manager_unpacker.return_value = [entry_mock]

        # run
        volumes = base_manager.all()

        # make the needed assertions
        p_base_manager_unpacker.assert_called_with([entry_mock])
        assert volumes == [entry_mock]
        p_etcd_client_read.assert_called_with(BaseManager.KEY, sorted=True)

    def test_by_id_key_not_found(self, base_manager, p_etcd_client_read):
        p_etcd_client_read.side_effect = etcd.EtcdKeyNotFound

        volume = base_manager.by_id('1')

        assert volume is None
        p_etcd_client_read.assert_called_with('/{}/{}'.format(base_manager.KEY, '1'))

    def test_by_id(self, p_etcd_client_read, p_base_manager_unpacker, base_manager, mocker):
        etcd_result_mock = mocker.MagicMock()
        p_etcd_client_read.side_effect = etcd_result_mock
        p_base_manager_unpacker.return_value = [etcd_result_mock]

        volume = base_manager.by_id('1')

        assert volume == etcd_result_mock
        p_etcd_client_read.assert_called_with('/{}/{}'.format(BaseManager.KEY, '1'))

    @mark.parametrize('suffix', ['', 'suffix'])
    def test_volume_create(self, suffix, p_etcd_client_write, p_base_schema_dumps, p_base_manager_unpacker,
                           base_manager, mocker):
        p_base_schema_dumps.return_value = ('{}', {})
        etcd_result_mock = mocker.MagicMock(name='', value='{}')
        p_etcd_client_write.return_value = etcd_result_mock
        p_base_manager_unpacker.return_value = [etcd_result_mock]

        result = base_manager.create({}, suffix=suffix)

        append = True if suffix == '' else False
        p_base_schema_dumps.assert_called_with({})
        p_etcd_client_write.assert_called_with('/{}/{}'.format(BaseManager.KEY, suffix),
                                               p_base_schema_dumps.return_value[0],
                                               append=append)
        p_base_manager_unpacker.assert_called_with([etcd_result_mock])
        assert result == etcd_result_mock

    @mark.parametrize('error', [etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound])
    def test_volume_update_etcd_errors(self, p_etcd_client_update, p_base_schema_dumps, base_manager, error):
        p_base_schema_dumps.return_value = ({'name': 'test'}, {})

        p_etcd_client_update.side_effect = error
        output_volume = base_manager.update(dummy_ready_volume)

        assert not output_volume
        assert p_etcd_client_update.called

    def test_volume_update_etcd(self, p_etcd_client_update, base_manager, p_base_manager_unpacker, p_base_schema_dumps):
        p_base_schema_dumps.return_value = ({'name': 'test'}, {})
        p_etcd_client_update.update.return_value = dummy_ready_volume
        p_base_manager_unpacker.return_value = [dummy_ready_volume]

        output_volume = base_manager.update(dummy_ready_volume)

        assert output_volume
        assert output_volume.unpacked_value == dummy_ready_volume.unpacked_value

    def test_volume_unpack(self, base_manager, p_base_schema_loads, mocker):
        data_mock_1 = mocker.MagicMock(value='')
        data_mock_2 = mocker.MagicMock(value='{"random": "foobar"}')
        p_base_schema_loads.side_effect = [({}, {}), ({'random': 'foobar'}, {}), RuntimeError]

        base_manager._unpack([data_mock_1, data_mock_2])

        call = mock_module.call
        p_base_schema_loads.assert_has_calls([call(data_mock_1.value), call(data_mock_2.value)])
        assert data_mock_1.unpacked_value == {}
        assert data_mock_2.unpacked_value == {'random': 'foobar'}
