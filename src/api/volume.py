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

from flask import current_app as app, request
from flask_restful import Resource

from models.manager import VolumeSchema, VolumeAttributeSchema


class Volume(Resource):
    """FlaskRestful API controller and resource handler for one specific volume"""

    @staticmethod
    def get(volume_id):
        """Returns a volume dict as a json response or 404 if not found

        Args:
            volume_id (str): The id parsed from the URL

        Returns (tuple): payload, http status code

        """
        manager = app.volume_manager
        volume = manager.by_id(volume_id)

        if volume is None:
            return {'message': 'Not Found'}, 404

        result, _ = VolumeSchema().dump(volume)
        return result, 200

    @staticmethod
    def put(volume_id):
        """Edits a volume dict based on the given representation

        Expects to receive a json payload with a complete new version of the volume to be edited

        Args:
            volume_id (str): The id parsed from the URL

        Returns (tuple): payload, http status code, headers

        """
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
        """Deletes the volume pointed by the id

        Args:
            volume_id (str): The id parsed from the URL

        Returns (tuple): payload, http status code, headers

        """
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
            lock.release()
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
    """FlaskRestful API controller and resource handler for the entire volume endpoint"""

    @staticmethod
    def get():
        """It will return a list of all the volumes

        Returns (tuple): payload, http status code

        """
        result, errors = VolumeSchema().dump(app.volume_manager.all()[1], many=True)
        return result

    @staticmethod
    def post():
        """It will create a volume with the given input as a starting point

        Returns (tuple): payload, http status code, headers

        """
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

        if id:
            lock.acquire(timeout=0, lock_ttl=10)

            data['state'] = 'pending'
            parent = manager.by_id(id)
            if not parent:
                lock.release()
                return {'message': 'Parent does not exist. Clone not created'}, 400

            parent_state = parent.value['state']
            if parent_state in ['deleting', 'scheduling']:
                lock.release()
                return {'message': 'Parent can\'t have state {} '
                                   'in order to clone'.format(parent_state)}, 400

        volume = manager.create(data)
        if id:
            lock.release()

        result, _ = VolumeSchema().dump(volume)
        return result, 202, {'Location': app.api.url_for(Volume, volume_id=result['id'])}
