import pytest

from flask import json

from models.volume_manager import volume_schema
from tests.integration.conftest import ClientVolumeSchema


class TestVolume:
    def test_volume_list_get(self, etcd_client, volume_raw_ok_ready, flask_app):
        generators = [volume_raw_ok_ready, volume_raw_ok_ready]

        volume_writes = []
        for generator in generators:
            volume_writes.append(etcd_client.write('volumes', generator, append=True))
        volume_writes = flask_app.volume_manager._unpack(volume_writes)

        expected, errors = volume_schema.dump(volume_writes, many=True)
        assert errors == {}

        with flask_app.test_client() as c:
            response = c.get('/volumes')
            assert response.status_code == 200

            actual, errors = ClientVolumeSchema().loads(response.data.decode(), many=True)

        assert errors == {}
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
        expected_result = {'error': '',
                           'error_count': 0,
                           'meta': {},
                           'name': '',
                           'requested': {'constraints': [], 'reserved_size': 1},
                           'actual': {},
                           'state': 'registered'}
        expected_code = 202

        with flask_app.test_client() as c:
            response = c.post('/volumes', data=volume_raw_minimal, content_type='application/json')

            result = json.loads(response.data.decode())
            id = result.pop('id')

            assert id
            assert response.status_code == expected_code
            assert expected_result == result
            assert response.headers['Location'] == 'http://localhost/volumes/{}'.format(id)

    def test_volume_list_post_read_only_and_extra_body(self, volume_raw_read_only_extra, flask_app):
        expected_result = {'error': '',
                           'error_count': 0,
                           'meta': {"instance.name": "test_instance"},
                           'name': 'ok',
                           'requested': {'constraints': [], 'reserved_size': 10},
                           'actual': {},
                           'state': 'registered'}

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

        volume = flask_app.volume_manager._unpack([volume])[0]
        expected, errors = volume_schema.dump(volume)
        assert errors == {}

        with flask_app.test_client() as c:
            response = c.get('/volumes/{}'.format(id))

            actual, errors = ClientVolumeSchema().loads(response.data.decode())

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
        to_delete = etcd_client.write('volumes', volume_raw_ok_deleting, append=True)
        id = flask_app.volume_manager.get_id_from_key(to_delete.key)

        with flask_app.test_client() as c:
            func = getattr(c, method)
            response = func('/volumes/{}'.format(id))

            result = json.loads(response.data.decode())

            assert response.status_code == 409
            assert expected_message == result

    # TODO test put on client after unpack

