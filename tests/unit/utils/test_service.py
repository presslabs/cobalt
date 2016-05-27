from pytest import mark, raises


@mark.parametrize('method', ['start', 'stop'])
class TestService:
    def test_has_method(self, method, service):
        assert hasattr(service, method)
        assert callable(getattr(service, method))

    def test_method_unimplemented(self, method, service):
        func = getattr(service, method)

        with raises(NotImplementedError):
            func()
