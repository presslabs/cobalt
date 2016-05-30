from flask import current_app as app, request
from flask_restful import Resource

from models import volume_attribute_schema, volume_schema, VolumeSchema


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

        if volume.unpacked_value.get('state') != 'ready':
            return {'message': 'Resource not in ready state, can\'t update.'}, 409

        new_volume, errors = volume_attribute_schema.load(request.get_json(force=True))
        if errors:
            return {'message': errors}, 400

        if volume.unpacked_value['requested'] == new_volume:
            return '', 304

        volume.unpacked_value['requested'] = new_volume

        volume = manager.update(volume)
        if not volume:
            return {'message': 'Resource changed during transition.'}, 409

        result, _ = volume_schema.dump(volume)
        return result, 202, {'Location': app.api.url_for(Volume, volume_id=volume.unpacked_value['id'])}

    @staticmethod
    def delete(volume_id):
        manager = app.volume_manager

        volume = manager.by_id(volume_id)
        if volume is None:
            return {'message': 'Not Found'}, 404

        if volume.unpacked_value.get('state') != 'ready':
            return {'message': 'Resource not in ready state, can\'t delete.'}, 409

        volume.unpacked_value['state'] = 'deleting'
        volume = manager.update(volume)

        if not volume:
            return {'message': 'Resource changed during transition.'}, 409

        result, _ = volume_schema.dump(volume)
        return result, 202, {'Location': app.api.url_for(Volume, volume_id=result['id'])}


class VolumeList(Resource):
    @staticmethod
    def get():
        result, _ = volume_schema.dump(app.volume_manager.all(), many=True)
        return result

    @staticmethod
    def post():
        manager = app.volume_manager

        fields = ('name', 'meta', 'requested',)
        data, errors = VolumeSchema(only=fields).load(request.get_json(force=True))
        if errors:
            return {'message': errors}, 400

        data['errors'] = ''
        data['error_count'] = 0,
        data['node'] = ''
        data['state'] = 'registered'
        data['actual'] = {}

        volume = manager.create(data)

        result, _ = volume_schema.dump(volume)
        return result, 202, {'Location': app.api.url_for(Volume, volume_id=result['id'])}

