from flask import current_app
from flask_restful import Resource, fields, marshal_with, marshal

from utils.marshaller import PrefixRemovedString
from models.volume import Volume as VolumeModel

volume_marshaller = {
    'id': PrefixRemovedString(attribute='key', prefix='/{}/'.format(VolumeModel.KEY)),
    'name': fields.String(attribute=lambda x: x.value['name'], default='')
}


class Volume(Resource):
    def get(self, volume_id):
        volume_manager = current_app.volume_manager
        volume = volume_manager.by_id(volume_id)

        if volume:
            return marshal(volume, volume_marshaller), 200

        return {'message': 'Not Found'}, 404

    def put(self, volume_id):
        pass

    def delete(self, volume_id):
        pass


class VolumeList(Resource):
    @marshal_with(volume_marshaller)
    def get(self):
        volume_manager = current_app.volume_manager

        return volume_manager.all()

    def post(self):
        pass
