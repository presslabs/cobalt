from flask import current_app
from flask_restful import Resource

from api.app import api
from models.volume_manager import volume_schema


class Volume(Resource):
    def get(self, volume_id):
        volume_manager = current_app.volume_manager
        volume = volume_manager.by_id(volume_id)

        if volume is None:
            return {'message': 'Not Found'}, 404

        result, _ = volume_schema.dump(volume)
        return result, 200

    def put(self, volume_id):
        pass

    def delete(self, volume_id):
        volume_manager = current_app.volume_manager

        volume = volume_manager.by_id(volume_id)
        if volume is None:
            return {'message': 'Not Found'}, 404

        if volume.unpacked_value.get('state', 'undefined') != 'ready':
            return {'message': 'Resource not in ready state, can\'t delete.'}, 409

        volume.unpacked_value['state'] = 'deleting'
        volume = volume_manager.update(volume)

        if not volume:
            return {'message': 'Resource changed during transition.'}, 409

        result, _ = volume_schema.dump(volume)
        return result, 202, {'Location': api.url_for(Volume, volume_id=volume.unpacked_value['id'])}


class VolumeList(Resource):
    def get(self):
        volume_manager = current_app.volume_manager

        result, _ = volume_schema.dump(volume_manager.all(), many=True)
        return result

    def post(self):
        pass


def register_resources(flask_restful):
    flask_restful.add_resource(VolumeList, '/volumes')
    flask_restful.add_resource(Volume, '/volumes/<volume_id>')