import pytest


@pytest.mark.parametrize('method', ['start', 'stop'])
class TestService:
    def test_has_method(self, method, service):
        assert hasattr(service, method)
        assert callable(getattr(service, method))

    def test_method_unimplemented(self, method, service):
        func = getattr(service, method)

        with pytest.raises(NotImplementedError):
            func()