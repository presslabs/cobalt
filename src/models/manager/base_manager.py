import etcd
from flask import json
from marshmallow import Schema


class BaseSchema(Schema):
    pass


class BaseManager:
    KEY = ''

    def __init__(self, client):
        self.client = client

        try:
            self.client.write(self.KEY, '', dir=True)
        except (etcd.EtcdAlreadyExist, etcd.EtcdNotFile):
            pass

    def all(self):
        try:
            dir = self.client.read(self.KEY, sorted=True)
            entries = [entry for entry in dir.leaves if not entry.dir]
        except etcd.EtcdKeyNotFound:
            dir = None
            entries = []

        return dir, self._load_from_etcd(entries)

    def all_keys(self):
        return [entry.key for entry in self.all()[1]]

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

    def delete(self, entity):
        try:
            entity = self.client.delete(entity.key)
        except (etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound):
            return False

        return self._load_from_etcd(entity)

    def watch(self, index=None, timeout=0):
        try:
            entity = self.client.watch(BaseManager.KEY, recursive=True, index=index, timeout=timeout)
        except etcd.EtcdWatchTimedOut:
            return None
        return self._load_from_etcd(entity)

    @staticmethod
    def get_id_from_key(key):
        return key[len(BaseManager.KEY) + 2:]

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
