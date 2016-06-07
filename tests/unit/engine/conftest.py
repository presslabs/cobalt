# Copyright 2016 PressLabs SRL
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

from etcd import Lock
from pytest import fixture, mark

from engine import Engine, Lease, Executor


@fixture
@mark.usefixtures('p_create_leaser', 'p_create_lock', 'p_create_executor')
def engine(m_etcd_client, volume_manager, machine_manager):
    return Engine(m_etcd_client, volume_manager, machine_manager,
                  {'leaser': {'lease_ttl': 0, 'refresh_ttl': 0}, 'executor': {'timeout': 10}})


@fixture
def m_lock(mocker):
    return mocker.MagicMock(spec=Lock)


@fixture
def m_lease(mocker):
    return mocker.MagicMock(spec=Lease)


@fixture
def m_executor(mocker):
    return mocker.MagicMock(spec=Executor)


@fixture
def executor(volume_manager, machine_manager):
    return Executor(volume_manager, machine_manager, {'timeout': 0})


@fixture
def p_create_executor(mocker, engine):
    return mocker.patch.object(engine, '_create_executor')


@fixture
def p_engine_executor_timeout(mocker, engine):
    return mocker.patch.object(engine.executor, 'timeout')


@fixture
def p_engine_executor_reset(mocker, engine):
    return mocker.patch.object(engine.executor, 'reset')


@fixture
def p_executor_process(mocker, executor):
    return mocker.patch.object(executor, '_process')


@fixture
def p_executor_active_machines(mocker, executor):
    return mocker.patch.object(executor, 'get_active_machines')
