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

from flask import current_app as app, request
from flask_restful import Resource

from models.manager import VolumeSchema, VolumeAttributeSchema


class Volume(Resource):
    @staticmethod
    def get(volume_id):
        manager = app.volume_manager
        volume = manager.by_id(volume_id)

        if volume is None:
            return {'message': 'Not Found'}, 404

        result, _ = VolumeSchema().dump(volume)
        return result, 200

    @staticmethod
    def put(volume_id):
        manager = app.volume_manager

        volume = manager.by_id(volume_id)
        if volume is None:
            return {'message': 'Not Found'}, 404

        if volume.value['state'] != 'ready':
            return {'message': 'Resource not in ready state, can\'t update.'}, 409

        new_volume, errors = VolumeAttributeSchema().load(request.get_json(force=True))
        if errors:
            return {'message': errors}, 400

        if volume.value['requested'] == new_volume:
            return '', 304

        volume.value['requested'] = new_volume
        volume.value['state'] = 'pending'

        volume = manager.update(volume)
        if not volume:
            return {'message': 'Resource changed during transition.'}, 409

        result, _ = VolumeSchema().dump(volume)
        return result, 202, {'Location': app.api.url_for(Volume, volume_id=result['id'])}

    @staticmethod
    def delete(volume_id):
        manager = app.volume_manager

        target_volume = manager.by_id(volume_id)
        if target_volume is None:
            return {'message': 'Not Found'}, 404

        if target_volume.value['state'] != 'ready':
            return {'message': 'Resource not in ready state, can\'t delete.'}, 409

        lock = manager.get_lock(volume_id, 'clone')
        lock.acquire(timeout=0, lock_ttl=10)

        pending_clones = []
        for volume in manager.all()[1]:
            if volume.value['control']['parent_id'] == volume_id:
                pending_clones.append(manager.get_id_from_key(volume.key))

        if pending_clones:
            return {'message': 'Resource has pending clones, can\'t delete.',
                    'clones': pending_clones}, 409

        target_volume.value['state'] = 'deleting'
        target_volume = manager.update(target_volume)
        lock.release()

        if not target_volume:
            return {'message': 'Resource changed during transition.'}, 409

        result, _ = VolumeSchema().dump(target_volume)
        return result, 202, {'Location': app.api.url_for(Volume, volume_id=result['id'])}


class VolumeList(Resource):
    @staticmethod
    def get():
        result, errors = VolumeSchema().dump(app.volume_manager.all()[1], many=True)
        return result

    @staticmethod
    def post():
        manager = app.volume_manager
        request_json = request.get_json(force=True)

        id = request_json.get('id', '')

        fields = ('name', 'meta', 'requested',)
        data, errors = VolumeSchema(only=fields).load(request_json)
        if errors:
            return {'message': errors}, 400

        data['node'] = ''
        data['state'] = 'scheduling'
        data['actual'] = {}
        data['control'] = {
            'error': '',
            'error_count': 0,
            'parent_id': id
        }

        lock = manager.get_lock(id, 'clone')
        lock.acquire(timeout=0, lock_ttl=10)

        if id:
            data['state'] = 'pending'
            parent = manager.by_id(id)
            if not parent:
                return {'message': 'Parent does not exist. Clone not created'}, 400

        volume = manager.create(data)
        lock.release()

        result, _ = VolumeSchema().dump(volume)
        return result, 202, {'Location': app.api.url_for(Volume, volume_id=result['id'])}
