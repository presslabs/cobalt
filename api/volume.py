from flask import current_app, abort
from flask_restful import Resource

from models.volume_manager import volume_schema


class Volume(Resource):
    def get(self, volume_id):
        volume_manager = current_app.volume_manager
        volume = volume_manager.by_id(volume_id)

        if volume is None:
            abort(404)

        result, _ = volume_schema.dump(volume)
        return result, 200

    def put(self, volume_id):
        pass

    def delete(self, volume_id):
        pass


class VolumeList(Resource):
    def get(self):
        volume_manager = current_app.volume_manager

        result, _ = volume_schema.dump(volume_manager.all(), many=True)
        return result

    def post(self):
        pass
