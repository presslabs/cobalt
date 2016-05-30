from pytest import fixture

from models.base_manager import BaseManager, base_schema


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
def p_base_manager_update(mocker, base_manager):
    return mocker.patch.object(base_manager, 'create')


@fixture
def p_base_manager_unpacker(mocker, base_manager):
    return mocker.patch.object(base_manager, '_unpack')


@fixture
def p_base_schema_dumps(mocker):
    return mocker.patch.object(base_schema, 'dumps')


@fixture
def p_base_schema_loads(mocker):
    return mocker.patch.object(base_schema, 'loads')
