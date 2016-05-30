import etcd
from marshmallow import Schema


class BaseSchema(Schema):
    pass

base_schema = BaseSchema()


class BaseManager:
    KEY = ''
    SCHEMA = base_schema

    def __init__(self, client):
        self.client = client

    def all(self):
        try:
            entries = [entry for entry in self.client.read(self.KEY, sorted=True).leaves if not entry.dir]
        except etcd.EtcdKeyNotFound:
            entries = []

        return self._unpack(entries)

    def by_id(self, entry_id):
        try:
            entry = self.client.read('/{}/{}'.format(self.KEY, entry_id))
        except etcd.EtcdKeyNotFound:
            return None

        return self._unpack([entry])[0]

    def create(self, data, suffix=''):
        append = True if suffix == '' else False
        key = '/{}/{}'.format(self.KEY, suffix)

        entry, _ = self.SCHEMA.dumps(data)
        entry = self.client.write(key, entry, append=append)

        return self._unpack([entry])[0]

    def update(self, entity):
        entity.value, _ = self.SCHEMA.dumps(entity.unpacked_value)

        try:
            entity = self.client.update(entity)
        except (etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound):
            return False

        volume = self._unpack([entity])[0]

        return volume

    def _unpack(self, entries):
        # we trust that etcd data is valid
        for entry in entries:
            entry.unpacked_value, _ = self.SCHEMA.loads(entry.value)

        return entries
