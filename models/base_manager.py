import etcd
from flask import json
from marshmallow import Schema


class BaseSchema(Schema):
    pass


class BaseManager:
    KEY = ''

    def __init__(self, client):
        self.client = client

    def all(self):
        try:
            entries = [entry for entry in self.client.read(self.KEY, sorted=True).leaves if not entry.dir]
        except etcd.EtcdKeyNotFound:
            entries = []

        return self._load_from_etcd(entries)

    def by_id(self, entry_id):
        try:
            entry = self.client.read('/{}/{}'.format(self.KEY, entry_id))
        except etcd.EtcdKeyNotFound:
            return None

        return self._load_from_etcd(entry)

    def create(self, data, suffix=''):
        append = True if suffix == '' else False
        key = '/{}/{}'.format(self.KEY, suffix)

        entry = self.client.write(key, json.dumps(data), append=append)

        return self._load_from_etcd(entry)

    def update(self, entity):
        entity.value = json.dumps(entity.value)

        try:
            entity = self.client.update(entity)
        except (etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound):
            return False

        return self._load_from_etcd(entity)

    def _load_from_etcd(self, data):
        # we trust that etcd data is valid
        try:
            iter(data)
        except TypeError:
            data.value = json.loads(data.value)
            return data
        else:
            for e in data:
                e.value = json.loads(e.value)

        return data
