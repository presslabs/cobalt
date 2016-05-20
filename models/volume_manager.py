import etcd

from marshmallow import fields, Schema, utils


class Volume(object):
    KEY = 'volumes'

    def __init__(self, etcd_client):
        self.client = etcd_client

    def all(self):
        try:
            volumes = [volume for volume in self.client.get(Volume.KEY).leaves if not volume.dir]
        except etcd.EtcdKeyNotFound:
            volumes = []

        return self._unpack(volumes)

    def by_id(self, id):
        try:
            volume = self.client.get('/{}/{}'.format(Volume.KEY, id))
        except etcd.EtcdKeyNotFound:
            return None

        return self._unpack([volume])[0]

    def by_machine(self, machine_id):
        pass

    def by_status(self, status):
        data = []

        volumes = self.all()
        for entry in volumes:
            if 'state' in entry.unpacked_value and entry.unpacked_value['state'] == status:
                data.append(entry)
        return data

    def create(self, volume: dict):
        volume = packer_schema.dumps(volume).data
        volume = self.client.write(Volume.KEY, volume, append=True)
        volume = self._unpack([volume])[0]

        return volume

    def update(self, volume):
        volume.value, _ = PackerSchema().dumps(volume.unpacked_value)

        try:
            volume = self.client.update(volume)
        except (etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound):
            return False

        volume = self._unpack([volume])[0]
        # add id manually as it is ignored on load from json
        volume.unpacked_value['id'] = self.get_id_from_key(volume.key)

        return volume

    def _unpack(self, volumes):
        for volume in volumes:
            volume.unpacked_value, _ = volume_schema.loads(volume.value)

        return volumes

    @staticmethod
    def get_id_from_key(key):
        return key[len(Volume.KEY) + 2:]


class VolumeAttributeSchema(Schema):
    class Meta:
        ordered = True

    reserved_size = fields.Integer(required=True)
    constraints = fields.List(fields.String(), missing=[], default=[])


class PackerSchema(Schema):
    class Meta:
        ordered = True

    state = fields.String(default='registered', missing='registered')
    name = fields.String(default='', missing='registered')
    error = fields.String(default='', missing='')
    error_count = fields.Integer(default=0, missing=0)

    meta = fields.Dict(default={}, missing={})

    actual = fields.Nested(VolumeAttributeSchema, default={}, missing={})
    requested = fields.Nested(VolumeAttributeSchema, default={}, missing={})


class VolumeSchema(PackerSchema):
    class Meta:
        ordered = True

    id = fields.String(required=True)

    def get_attribute(self, attr, obj, default):
        if attr != 'id':
            return utils.get_value(attr, obj.unpacked_value, default)

        etcd_key = super(VolumeSchema, self).get_attribute('key', obj, default)
        id = Volume.get_id_from_key(etcd_key)

        return id

volume_schema = VolumeSchema()
packer_schema = PackerSchema()
