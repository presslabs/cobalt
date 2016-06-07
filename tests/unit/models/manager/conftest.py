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

from pytest import fixture

from models.manager.base_manager import BaseManager


@fixture
def base_manager(m_etcd_client):
    return BaseManager(m_etcd_client)


@fixture
def p_base_manager_all(mocker, base_manager):
    return mocker.patch.object(base_manager, 'all')


@fixture
def p_base_manager_by_id(mocker, base_manager):
    return mocker.patch.object(base_manager, 'by_id')


@fixture
def p_base_manager_update(mocker, base_manager):
    return mocker.patch.object(base_manager, 'update')


@fixture
def p_base_manager_all_keys(mocker, base_manager):
    return mocker.patch.object(base_manager, 'all_keys')


@fixture
def p_base_manager_update(mocker, base_manager):
    return mocker.patch.object(base_manager, 'create')


@fixture
def p_base_manager_load_from_etcd(mocker, base_manager):
    return mocker.patch.object(base_manager, '_load_from_etcd')
