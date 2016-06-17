# Copyright 2016 Presslabs SRL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import etcd

from pytest import fixture

from agent import Agent
from api import Api
from engine import Executor, Engine
from models.manager import VolumeManager, MachineManager
from models.driver import BTRFSDriver
from models.node import Node


@fixture
def flask_app(volume_manager):
    return Api._create_app(volume_manager)


@fixture
def volume_manager(etcd_client):
    return VolumeManager(etcd_client)


@fixture
def machine_manager(etcd_client):
    return MachineManager(etcd_client)


@fixture
def etcd_client(request):
    client = etcd.Client(version_prefix="/v2", host="127.0.0.1", port=4001)

    def fin():
        entrypoints = [
            VolumeManager.KEY,
            MachineManager.KEY,
            '_locks',
            'version']

        for entry in entrypoints:
            try:
                client.delete(entry, recursive=True)
            except etcd.EtcdException:
                pass

    request.addfinalizer(fin)
    return client


@fixture
def executor(volume_manager, machine_manager):
    return Executor(volume_manager, machine_manager, {'timeout': 2})


@fixture
def engine(etcd_client, machine_manager, volume_manager):
    return Engine(etcd_client, volume_manager, machine_manager, {
        'leaser': {
            'lease_ttl': 10,
            'refresh_ttl': 6,
        },
        'executor': {
            'timeout': 1
        }
    })


@fixture
def engine_factory(etcd_client, machine_manager, volume_manager):
    class Factory:
        def get(self):
            return Engine(etcd_client, volume_manager, machine_manager, {
                'leaser': {
                    'lease_ttl': 10,
                    'refresh_ttl': 6,
                },
                'executor': {
                    'timeout': 0.1
                }
            })
    return Factory()


@fixture(scope='module')
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
        },
        "control": {
            "error": "",
            "error_count": 0,
            "parent_id": ""
        }
    }'''


@fixture(scope='module')
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
        },
        "control": {
            "error": "",
            "error_count": 0
        }
    }'''


@fixture(scope='module')
def volume_raw_requested_ok():
    return '''{
        "reserved_size": 100,
        "constraints": []
    }'''


@fixture(scope='module')
def volume_raw_requested_extra():
    return '''{
        "reserved_size": 100,
        "constraints": [],
        "extra": false
    }'''


@fixture(scope='module')
def volume_raw_empty():
    return ''


@fixture(scope='module')
def volume_raw_minimal():
    return '''
        {
            "requested": {
                "reserved_size": 1,
                "constraints": []
            }
        }
    '''


@fixture(scope='module')
def volume_raw_read_only_extra():
    return '''{
        "id": "",
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
        "control": {
            "error": "random",
            "error_count": 1
        }
    }'''


@fixture
def volume_raw_ready_assigned():
    return '''{
        "node": "test-node",
        "state": "ready",
        "requested": {
            "reserved_size": 1,
            "constraints": ["ssd"]
        },
        "actual": {
            "reserved_size": 1,
            "constraints": ["ssd"]
        },
        "control": {
            "error": "",
            "error_count": 0,
            "parent_id": ""
        }
    }'''


@fixture
def volume_raw_scheduling_assigned():
    return '''{
        "node": "test-node",
        "state": "scheduling",
        "requested": {"constraints": ["ssd"], "reserved_size": 1},
        "actual": {},
        "control": {
            "error": "",
            "error_count": 0,
            "parent_id": ""
        }
    }'''


@fixture
def volume_raw_resizing_assigned():
    return '''{
        "node": "test-node",
        "state": "resizing",
        "requested": {
            "reserved_size": 2,
            "constraints": ["ssd"]
        },
        "actual": {
            "reserved_size": 1,
            "constraints": ["ssd"]
        },
        "control": {
            "error": "",
            "error_count": 0,
            "parent_id": ""
        }
    }'''


@fixture
def volume_raw_cloning_assigned():
    return '''{
        "node": "test-node",
        "state": "cloning",
        "requested": {
            "reserved_size": 1,
            "constraints": ["ssd"]
        },
        "control": {
            "error": "",
            "error_count": 0,
            "parent_id": ""
        }
    }'''


@fixture
def volume_raw_deleting_assigned():
    return '''{
        "node": "test-node",
        "state": "deleting",
        "actual": {
            "reserved_size": 1,
            "constraints": ["ssd"]
        },
        "requested": {
            "reserved_size": 1,
            "constraints": ["ssd"]
        },
        "control": {
            "error": "",
            "error_count": 0,
            "parent_id": ""
        }
    }'''


@fixture
def driver(request):
    i_driver = BTRFSDriver('/mnt')

    def fin():
        ids = i_driver.get_all()
        for id in ids:
            i_driver.remove(id)

    request.addfinalizer(fin)
    return i_driver


@fixture
def node(driver):
    node_conf = {
        'conf_path': '/etc/cobalt.conf',
        'volume_path': '/mnt',
        'max_fill': 0.8,
        'conf': {
            'name': 'test-node',
            'labels': ['ssd']
        }
    }

    return Node(node_conf, driver)


@fixture
def agent(machine_manager, volume_manager):
    return Agent(machine_manager, volume_manager, {
        'agent_ttl': 60,
        'max_error_count': 3,
        'max_error_timeout': 10,
        'node': {
            'volume_path': '/mnt',
            'conf_path': '/etc/cobalt.conf',
            'max_fill': 0.8,
            'conf': {
                'name': 'test-node',
                'labels': ['ssd']
            }
        },
        'watch_timeout': 10
    })
