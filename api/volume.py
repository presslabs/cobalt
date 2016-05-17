from flask import current_app
from flask_restful import Resource, fields, marshal_with

from utils.marshaller import PrefixRemovedString
from models.volume import Volume as VolumeModel

volume_marshaller = {
    'id': PrefixRemovedString(attribute='key', prefix='/{}/'.format(VolumeModel.KEY)),
    'name': fields.String(attribute=lambda x: x.value['name'], default='')
}


class Volume(Resource):
    def get(self, volume_id):
        pass

    def put(self, volume_id):
        pass

    def delete(self, volume_id):
        pass


class VolumeList(Resource):
    @marshal_with(volume_marshaller)
    def get(self):
        volume_manager = current_app.volume_manager

        return volume_manager.all(), 200

    def post(self):
        pass
