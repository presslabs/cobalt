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

import pytest
from flask import json

from models.manager import VolumeSchema, VolumeAttributeSchema


class TestVolumeIntegration:
    def test_volume_list_get(self, etcd_client, volume_raw_ok_ready, flask_app):
        generators = [volume_raw_ok_ready, volume_raw_ok_ready]

        volume_writes = []
        for generator in generators:
            volume_writes.append(etcd_client.write('volumes', generator, append=True))
        volume_writes = flask_app.volume_manager._load_from_etcd(volume_writes)

        expected, errors = VolumeSchema().dump(volume_writes, many=True)
        assert errors == {}

        with flask_app.test_client() as c:
            response = c.get('/volumes')
            assert response.status_code == 200

            actual = json.loads(response.data.decode())

        assert len(actual) == len(expected)
        assert actual == expected

    def test_volume_list_post_empty_body_no_json(self, volume_raw_empty, flask_app):
        with flask_app.test_client() as c:
            response = c.post('/volumes', data=volume_raw_empty)
            assert response.status_code == 400

    def test_volume_list_post_empty_body(self, flask_app):
        expected_result = {'message': {'requested': {'constraints': ['Missing data for required field.'],
                                                     'reserved_size': ['Missing data for required field.']}}}
        expected_code = 400

        with flask_app.test_client() as c:
            response = c.post('/volumes', data='{}', content_type='application/json')

            result = json.loads(response.data.decode())

            assert response.status_code == expected_code
            assert expected_result == result

    def test_volume_list_post_minimal_body(self, volume_raw_minimal, flask_app):
        expected_result = {
            'meta': {},
            'name': '',
            'requested': {'constraints': [], 'reserved_size': 1},
            'actual': {},
            'node': '',
            'state': 'scheduling',
            'control': {
                'error': '',
                'error_count': 0,
                'parent_id': ''
            }
        }

        expected_code = 202

        with flask_app.test_client() as c:
            response = c.post('/volumes', data=volume_raw_minimal, content_type='application/json')

            result = json.loads(response.data.decode())
            id = result.pop('id')

            assert id
            assert response.status_code == expected_code
            assert expected_result == result
            assert response.headers['Location'] == 'http://localhost/volumes/{}'.format(id)

    def test_post_clone(self, volume_raw_minimal, flask_app):
        expected_result = {
            'meta': {},
            'name': '',
            'requested': {'constraints': [], 'reserved_size': 1},
            'actual': {},
            'node': '',
            'state': 'pending',
            'control': {
                'error': '',
                'error_count': 0,
                'parent_id': ''
            }
        }

        expected_code = 202

        with flask_app.test_client() as c:
            # create parent and make
            response = c.post('/volumes', data=volume_raw_minimal, content_type='application/json')
            result = json.loads(response.data.decode())
            id = result.pop('id')
            expected_result['control']['parent_id'] = str(id)

            # create clone
            request = {'id': str(id), 'requested': {'reserved_size': 1, 'constraints': []}}
            response = c.post('/volumes', data=json.dumps(request), content_type='application/json')
            result = json.loads(response.data.decode())
            id = result.pop('id')

            assert id
            assert response.status_code == expected_code
            assert expected_result == result
            assert response.headers['Location'] == 'http://localhost/volumes/{}'.format(id)

    def test_volume_list_post_read_only_and_extra_body(self, volume_raw_read_only_extra, flask_app):
        expected_result = {
            'meta': {"instance.name": "test_instance"},
            'name': 'ok',
            'requested': {'constraints': [], 'reserved_size': 10},
            'actual': {},
            'node': '',
            'state': 'scheduling',
            'control': {
                'error': '',
                'error_count': 0,
                'parent_id': ''
            }
        }

        expected_code = 202

        with flask_app.test_client() as c:
            response = c.post('/volumes', data=volume_raw_read_only_extra, content_type='application/json')

            assert response.status_code == expected_code

            result = json.loads(response.data.decode())
            id = result.pop('id')

            assert id
            assert id != 'random'
            assert expected_result == result
            assert response.headers['Location'] == 'http://localhost/volumes/{}'.format(id)

    def test_volume_delete(self, etcd_client, volume_raw_ok_ready, flask_app):
        to_delete = etcd_client.write('volumes', volume_raw_ok_ready, append=True)
        id = flask_app.volume_manager.get_id_from_key(to_delete.key)

        with flask_app.test_client() as c:
            response = c.delete('/volumes/{}'.format(id))

            result = json.loads(response.data.decode())

            assert result['id'] == id
            assert result['state'] == 'deleting'
            assert response.status_code == 202
            assert response.headers['Location'] == 'http://localhost/volumes/{}'.format(id)

    def test_volume_get(self, etcd_client, volume_raw_ok_ready, flask_app):
        volume = etcd_client.write('volumes', volume_raw_ok_ready, append=True)
        id = flask_app.volume_manager.get_id_from_key(volume.key)

        volume = flask_app.volume_manager._load_from_etcd([volume])[0]
        expected, errors = VolumeSchema().dump(volume)
        assert errors == {}

        with flask_app.test_client() as c:
            response = c.get('/volumes/{}'.format(id))

            actual = json.loads(response.data.decode())

            assert actual == expected
            assert response.status_code == 200

    @pytest.mark.parametrize('method', ['put', 'get', 'delete'])
    def test_volume_not_found(self, method, flask_app):
        with flask_app.test_client() as c:
            func = getattr(c, method)
            response = func('/volumes/0')

            result = json.loads(response.data.decode())

            assert result == {'message': 'Not Found'}
            assert response.status_code == 404

    @pytest.mark.parametrize('method,expected_message', [
        ['put', {'message': 'Resource not in ready state, can\'t update.'}],
        ['delete', {'message': 'Resource not in ready state, can\'t delete.'}]
    ])
    def test_volume_invalid_state(self, method, expected_message, etcd_client, volume_raw_ok_deleting, flask_app):
        volume = etcd_client.write('volumes', volume_raw_ok_deleting, append=True)
        id = flask_app.volume_manager.get_id_from_key(volume.key)

        with flask_app.test_client() as c:
            func = getattr(c, method)
            response = func('/volumes/{}'.format(id))

            result = json.loads(response.data.decode())

            assert response.status_code == 409
            assert expected_message == result

    def test_volume_put_empty_body_no_json(self, etcd_client, volume_raw_ok_ready, volume_raw_empty, flask_app):
        volume = etcd_client.write('volumes', volume_raw_ok_ready, append=True)
        id = flask_app.volume_manager.get_id_from_key(volume.key)

        with flask_app.test_client() as c:
            response = c.put('/volumes/{}'.format(id), data=volume_raw_empty)
            assert response.status_code == 400

    def test_volume_put_empty_body(self, etcd_client, volume_raw_ok_ready, flask_app):
        volume = etcd_client.write('volumes', volume_raw_ok_ready, append=True)
        id = flask_app.volume_manager.get_id_from_key(volume.key)

        expected_result = {'message': {'constraints': ['Missing data for required field.'],
                                       'reserved_size': ['Missing data for required field.']}}

        expected_code = 400

        with flask_app.test_client() as c:
            response = c.put('/volumes/{}'.format(id), data='{}', content_type='application/json')

            result = json.loads(response.data.decode())

            assert response.status_code == expected_code
            assert expected_result == result

    def test_volume_put_not_modified(self, etcd_client, volume_raw_ok_ready, flask_app):
        volume = etcd_client.write('volumes', volume_raw_ok_ready, append=True)
        id = flask_app.volume_manager.get_id_from_key(volume.key)

        data = json.loads(volume_raw_ok_ready)
        requested = json.dumps(data['requested'])

        with flask_app.test_client() as c:
            response = c.put('/volumes/{}'.format(id), data=requested, content_type='application/json')

            assert response.status_code == 304

    def test_volume_put_minimal_body(self, etcd_client, volume_raw_ok_ready,
                                     volume_raw_requested_ok, flask_app):
        volume = etcd_client.write('volumes', volume_raw_ok_ready, append=True)
        id = flask_app.volume_manager.get_id_from_key(volume.key)

        volume = flask_app.volume_manager._load_from_etcd([volume])[0]
        expected, errors = VolumeSchema().dump(volume)
        assert errors == {}

        expected['state'] = 'pending'
        expected['requested'], errors = VolumeAttributeSchema().loads(volume_raw_requested_ok)
        assert errors == {}

        with flask_app.test_client() as c:
            response = c.put('/volumes/{}'.format(id), data=volume_raw_requested_ok,
                             content_type='application/json')

            result, errors = VolumeSchema().loads(response.data.decode())

            assert errors == {}
            assert result['id'] == id
            assert response.status_code == 202
            assert expected == result
            assert response.headers['Location'] == 'http://localhost/volumes/{}'.format(id)

    def test_volume_put_extra_body(self, etcd_client, volume_raw_ok_ready, volume_raw_requested_extra, flask_app):
        volume = etcd_client.write('volumes', volume_raw_ok_ready, append=True)
        id = flask_app.volume_manager.get_id_from_key(volume.key)

        volume = flask_app.volume_manager._load_from_etcd([volume])[0]
        expected, errors = VolumeSchema().dump(volume)
        assert errors == {}

        expected['state'] = 'pending'
        expected['requested'], errors = VolumeAttributeSchema().loads(volume_raw_requested_extra)
        assert errors == {}

        with flask_app.test_client() as c:
            response = c.put('/volumes/{}'.format(id), data=volume_raw_requested_extra,
                             content_type='application/json')

            result = json.loads(response.data.decode())

            assert result['id'] == id
            assert response.status_code == 202
            assert expected == result
            assert response.headers['Location'] == 'http://localhost/volumes/{}'.format(id)
