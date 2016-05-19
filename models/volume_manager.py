import etcd

from marshmallow import fields, Schema, utils


class Volume(object):
    KEY = 'volumes'

    def __init__(self, etcd_client):
        self.client = etcd_client

    def all(self):
        try:
            volumes = [volume for volume in self.client.get(Volume.KEY).leaves if not volume.dir]
        except:
            volumes = []

        return self._unpack(volumes)

    def by_id(self, id):
        try:
            volume = self.client.get('/{}/{}'.format(Volume.KEY, id))
        except:
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

    def create(self, volume=None):
        pass
        # if volume is None:
        #     volume = {}
        #
        # volume['state'] = 'registered'
        # volume['labels'] = {}
        # volume['requested'] = {}
        # volume['actual'] = {}
        #
        # self.client.write()

    def _unpack(self, volumes):
        for volume in volumes:
            volume.unpacked_value, _ = volume_schema.loads(volume.value)

        return volumes


class VolumeAttributeSchema(Schema):
    class Meta:
        ordered = True

    reserved_size = fields.Integer(required=True)
    constraints = fields.List(fields.String(required=False))


class VolumeSchema(Schema):
    class Meta:
        ordered = True

    id = fields.String(required=True, dump_only=True)
    state = fields.String(default='registered')
    name = fields.String(default='')
    error = fields.String(default='')
    error_count = fields.Integer(default=0)

    meta = fields.Dict(default={})

    actual = fields.Nested(VolumeAttributeSchema, default=[])
    requested = fields.Nested(VolumeAttributeSchema, default=[])

    def get_attribute(self, attr, obj, default):
        if attr != 'id':
            return utils.get_value(attr, obj.unpacked_value, default)

        etcd_key = super(VolumeSchema, self).get_attribute('key', obj, default)
        etcd_key = etcd_key[len(Volume.KEY) + 2:]

        return etcd_key

volume_schema = VolumeSchema()
