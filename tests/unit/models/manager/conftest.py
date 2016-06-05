from pytest import fixture

from models.manager.base_manager import BaseManager


@fixture
def base_manager(m_etcd_client):
    return BaseManager(m_etcd_client)


@fixture
def p_base_manager_all(mocker, base_manager):
    return mocker.patch.object(base_manager, 'all')


@fixture
def p_base_manager_by_id(mocker, base_manager):
    return mocker.patch.object(base_manager, 'by_id')


@fixture
def p_base_manager_update(mocker, base_manager):
    return mocker.patch.object(base_manager, 'update')


@fixture
def p_base_manager_all_keys(mocker, base_manager):
    return mocker.patch.object(base_manager, 'all_keys')


@fixture
def p_base_manager_update(mocker, base_manager):
    return mocker.patch.object(base_manager, 'create')


@fixture
def p_base_manager_load_from_etcd(mocker, base_manager):
    return mocker.patch.object(base_manager, '_load_from_etcd')
