import pytest

from utils import ReadOnlyDict


@pytest.fixture
def ro_dictionary():
    return ReadOnlyDict({'test': [1, 2, 3], 'foo': 'bar'})


class TestReadOnlyDict:
    def test_pop(self, ro_dictionary):
        with pytest.raises(RuntimeError):
            ro_dictionary.pop('test')

    def test_popitem(self, ro_dictionary):
        with pytest.raises(RuntimeError):
            ro_dictionary.popitem()

    def test_clear(self, ro_dictionary):
        with pytest.raises(RuntimeError):
            ro_dictionary.clear()

    def test_update(self, ro_dictionary):
        with pytest.raises(RuntimeError):
            ro_dictionary.update({'fizz': 'buzz'})

    def test_setdefault(self, ro_dictionary):
        with pytest.raises(RuntimeError):
            ro_dictionary.setdefault('test', None)

    def test_setitem(self, ro_dictionary):
        with pytest.raises(RuntimeError):
            ro_dictionary['test'] = None

    def test_getitem(self, ro_dictionary):
        assert ro_dictionary['test'] == [1, 2, 3]

    def test_del(self, ro_dictionary):
        with pytest.raises(RuntimeError):
            del ro_dictionary['test']
