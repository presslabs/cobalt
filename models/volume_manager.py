import etcd
from marshmallow import fields, Schema, validate, utils

from .base_manager import BaseManager
from time import time


class VolumeAttributeSchema(Schema):
    class Meta:
        ordered = True

    reserved_size = fields.Integer(required=True, validate=[validate.Range(min=0)])
    constraints = fields.List(fields.String(validate=[validate.Length(min=1)]), required=True)


class VolumeControlSchema(Schema):
    class Meta:
        ordered = True

    error = fields.String(default='', missing='')
    error_count = fields.Integer(default=0, missing=0)
    parent_id = fields.String(default='', missing='')


class VolumeSchema(Schema):
    class Meta:
        ordered = True

    id = fields.String(required=True)
    state = fields.String(default='scheduling', missing='scheduling')
    name = fields.String(default='', missing='')
    node = fields.String(default='', missing='')

    meta = fields.Dict(default={}, missing={})

    actual = fields.Nested(VolumeAttributeSchema, missing={}, default={})
    requested = fields.Nested(VolumeAttributeSchema, required=True)
    control = fields.Nested(VolumeControlSchema, required=True)

    def get_attribute(self, attr, obj, default):
        if attr == 'id':
            return VolumeManager.get_id_from_key(obj.key)
        return utils.get_value(attr, obj.value, default)


class VolumeManager(BaseManager):
    KEY = 'volumes'

    def by_states(self, states=None):
        volumes = self.all()[1]
        return VolumeManager.filter_states(volumes, states)

    def update(self, volume):
        volume.value['control']['update'] = time()
        volume = super(VolumeManager, self).update(volume)

        if not volume:
            return False

        return volume

    def create(self, data, *unused):
        data['control']['update'] = time()
        volume = super(VolumeManager, self).create(data, '')

        return volume

    @staticmethod
    def filter_states(volumes, states):
        states = states or []
        states = [states] if not isinstance(states, list) else states

        return [volume for volume in volumes if volume.value['state'] in states]
