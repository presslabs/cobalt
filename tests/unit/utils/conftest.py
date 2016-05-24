import pytest

from utils.service import Service


@pytest.fixture(scope='module')
def service():
    return Service()