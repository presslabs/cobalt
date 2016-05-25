import pytest

from api.api import Api
from utils import Service


class TestApi:
    def test_inherits_from_service(self):
        api_service = Api({})
        assert isinstance(api_service, Service)

    @pytest.mark.parametrize('method', ['start', 'stop'])
    def test_implements_from_service(self, method):
        assert Api.__dict__.get(method)


