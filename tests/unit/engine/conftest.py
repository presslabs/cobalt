from pytest import fixture

from engine import Engine


@fixture
def engine(lease, executor):
    return Engine(lease, executor)


@fixture
def lease(mocker):
    return mocker.MagicMock()


@fixture
def executor(mocker):
    return mocker.MagicMock()
