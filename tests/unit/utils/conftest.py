import pytest

from utils import Service, ReadOnlyDict


@pytest.fixture(scope='module')
def service():
    return Service()


@pytest.fixture
def ro_dictionary():
    return ReadOnlyDict({'test': [1, 2, 3], 'foo': 'bar'})