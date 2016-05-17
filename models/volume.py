import etcd

from json import dumps, loads


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
            volume.value = loads(volume.value)

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
        pass

    def reset_cache(self):
        self.volumes = []
