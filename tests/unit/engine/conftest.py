from pytest import fixture

from engine import Engine


@fixture
def engine(etcd, volume_manager):
    return Engine(etcd, volume_manager,
                  {'engine': {'leaser': {'lease_ttl': 0, 'refresh_ttl': 0}, 'executor': {'timeout': 10}}})


@fixture
def lease(mocker):
    return mocker.MagicMock()


@fixture
def executor(mocker):
    return mocker.MagicMock()
