import etcd
from marshmallow import fields, Schema, validate, utils

from .base_manager import BaseManager


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
        volume = super(VolumeManager, self).update(volume)

        if not volume:
            return False

        volume.value['id'] = self.get_id_from_key(volume.key)
        return volume

    def create(self, data, *unused):
        volume = super(VolumeManager, self).create(data, '')
        volume.value['id'] = self.get_id_from_key(volume.key)

        return volume

    def watch(self, index=None, timeout=0):
        try:
            volume = self.client.watch(VolumeManager.KEY, recursive=True, index=index, timeout=timeout)
        except etcd.EtcdWatchTimedOut:
            return None
        return super(VolumeManager, self)._load_from_etcd(volume)

    @staticmethod
    def get_id_from_key(key):
        return key[len(VolumeManager.KEY) + 2:]

    @staticmethod
    def filter_states(volumes, states):
        states = states or []
        states = [states] if not isinstance(states, list) else states

        return [volume for volume in volumes if volume.value['state'] in states]
