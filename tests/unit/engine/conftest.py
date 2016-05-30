from pytest import fixture, mark

from etcd import Lock
from engine import Engine, Lease, Executor


@fixture
@mark.usefixtures('p_create_leaser', 'p_create_lock', 'p_create_executor')
def engine(m_etcd_client, volume_manager):
    return Engine(m_etcd_client, volume_manager,
                  {'leaser': {'lease_ttl': 0, 'refresh_ttl': 0}, 'executor': {'timeout': 10}})


@fixture
def m_lock(mocker):
    return mocker.MagicMock(spec=Lock)


@fixture
def m_lease(mocker):
    return mocker.MagicMock(spec=Lease)


@fixture
def m_executor(mocker):
    return mocker.MagicMock(spec=Executor)


@fixture
def p_lease(mocker):
    return mocker.patch.object(Lease, '__init__')


@fixture
def p_executor(mocker):
    return mocker.patch.object(Executor, '__init__')


@fixture
def p_create_executor(mocker, engine):
    return mocker.patch.object(engine, '_create_executor')