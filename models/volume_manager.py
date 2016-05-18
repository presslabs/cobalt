import etcd

from marshmallow import fields, Schema, utils


class Volume(object):
    KEY = 'volumes'

    def __init__(self, etcd_client):
        self.client = etcd_client
        self.volumes = []

    def all(self):
        if self.volumes:
            return self.volumes

        try:
            self.volumes = [volume for volume in self.client.get(Volume.KEY).leaves if not volume.dir]
        except etcd.EtcdKeyNotFound:
            self.volumes = []

        for volume in self.volumes:
            volume.unpacked_value, _ = volume_schema.loads(volume.value)

        return self.volumes

    def by_id(self, id):
        volumes = self.all()
        for entry in volumes:
            if entry.key == '/{}/{}'.format(Volume.KEY, id):
                return entry

        return None

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

    def dump(self, volumes, schema: Schema):
        data = []
        for volume in volumes:
            data.append(schema.dump(volume.unpacked_value).data)
        return data

    def reset_cache(self):
        self.volumes = []


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
