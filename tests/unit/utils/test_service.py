from pytest import raises

from utils import Service


class TestService:
    def test_is_abstract(self):
        with raises(TypeError):
            Service()

    def test_has_start_stop_methods(self):
        assert list(Service.__abstractmethods__) == ['start', 'stop']
