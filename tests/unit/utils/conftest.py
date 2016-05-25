import pytest

from utils import Service


@pytest.fixture(scope='module')
def service():
    return Service()
