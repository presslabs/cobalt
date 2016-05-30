from marshmallow import fields, Schema, utils, validate

from .base_manager import BaseManager


class VolumeAttributeSchema(Schema):
    class Meta:
        ordered = True

    reserved_size = fields.Integer(required=True, validate=[validate.Range(min=0)])
    constraints = fields.List(fields.String(validate=[validate.Length(min=1)]), required=True)


class PackerSchema(Schema):
    class Meta:
        ordered = True

    state = fields.String(default='registered', missing='registered')
    name = fields.String(default='', missing='')
    node = fields.String(default='', missing='')
    error = fields.String(default='', missing='')
    error_count = fields.Integer(default=0, missing=0)

    meta = fields.Dict(default={}, missing={})

    actual = fields.Nested(VolumeAttributeSchema, missing={}, default={})
    requested = fields.Nested(VolumeAttributeSchema, required=True)


class VolumeSchema(PackerSchema):
    class Meta:
        ordered = True

    id = fields.String(required=True)

    def get_attribute(self, attr, obj, default):
        if attr != 'id':
            return utils.get_value(attr, obj.unpacked_value, default)

        etcd_key = super(VolumeSchema, self).get_attribute('key', obj, default)
        id = VolumeManager.get_id_from_key(etcd_key)

        return id


volume_schema = VolumeSchema()
packer_schema = PackerSchema()
volume_attribute_schema = VolumeAttributeSchema()


class VolumeManager(BaseManager):
    KEY = 'volumes'
    SCHEMA = packer_schema

    def by_state(self, state):
        return [volume for volume in self.all() if volume.unpacked_value.get('state') == state]

    def update(self, volume):
        volume = super(VolumeManager, self).update(volume)

        if not volume:
            return False

        volume.unpacked_value['id'] = self.get_id_from_key(volume.key)
        return volume

    def _unpack(self, volumes):
        # we trust that etcd data is valid
        for volume in volumes:
            volume.unpacked_value, _ = volume_schema.loads(volume.value)

        return volumes

    @staticmethod
    def get_id_from_key(key):
        return key[len(VolumeManager.KEY) + 2:]
