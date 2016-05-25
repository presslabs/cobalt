import pytest
import etcd

from models import Volume, PackerSchema, VolumeSchema
from cobalt import context


class ClientVolumeSchema(VolumeSchema):
    """
        Created just to check the output of the api and easily compare it with the generated one from etcd_result
    """
    class Meta:
        ordered = True

    def get_attribute(self, attr, obj, default):
        super(PackerSchema, self).get_attribute(attr, obj, default)


@pytest.fixture
def etcd_client(request):
    client = etcd.Client(**context['etcd'])

    def fin():
        entrypoints = [Volume.KEY, '_locks', 'machines']

        for entry in entrypoints:
            try:
                client.delete(entry, recursive=True)
            except etcd.EtcdException:
                pass

    request.addfinalizer(fin)
    return client


@pytest.fixture(scope='module')
def volume_raw_ok_ready():
    return '''{
        "name": "ok",
        "state": "ready",
        "requested": {
            "reserved_size": 10,
            "constraints": []
        },
        "actual": {
            "reserved_size": 2,
            "constraints": []
        },
        "meta": {
            "instance.name": "test_instance"
        }
    }'''


@pytest.fixture(scope='module')
def volume_raw_ok_deleting():
    return '''{
        "name": "ok",
        "state": "deleting",
        "requested": {
            "reserved_size": 10,
            "constraints": []
        },
        "actual": {
            "reserved_size": 2,
            "constraints": []
        },
        "meta": {
            "instance.name": "test_instance"
        }
    }'''


@pytest.fixture(scope='module')
def volume_raw_requested_ok():
    return '''{
        "reserved_size": 100,
        "constraints": []
    }'''


@pytest.fixture(scope='module')
def volume_raw_requested_extra():
    return '''{
        "reserved_size": 100,
        "constraints": [],
        "extra": false
    }'''


@pytest.fixture(scope='module')
def volume_raw_empty():
    return ''


@pytest.fixture(scope='module')
def volume_raw_minimal():
    return '''
        {
            "requested": {
                "reserved_size": 1,
                "constraints": []
            }
        }
    '''


@pytest.fixture(scope='module')
def volume_raw_read_only_extra():
    return '''{
        "id": "random",
        "name": "ok",
        "requested": {
            "reserved_size": 10,
            "constraints": []
        },
        "state": "rambo",
        "actual": {
            "reserved_size": 2,
            "constraints": []
        },
        "meta": {
            "instance.name": "test_instance"
        },
        "undefined": 1,
        "error": "random",
        "error_count": 1
    }'''
