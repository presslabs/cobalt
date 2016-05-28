from pytest import fixture

from utils import ReadOnlyDict


@fixture
def ro_dictionary():
    return ReadOnlyDict({'test': [1, 2, 3], 'foo': 'bar'})
