from pytest import fixture

from utils import Service, ReadOnlyDict


@fixture(scope='module')
def service():
    return Service()


@fixture
def ro_dictionary():
    return ReadOnlyDict({'test': [1, 2, 3], 'foo': 'bar'})
