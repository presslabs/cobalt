# -*- coding: utf-8 -*-
# vim: ft=python:sw=4:ts=4:sts=4:et:

import json

class Volume:
    REGISTRED = 'registred'
    PROVISIONED = 'provisioned'
    UNREGISTRED = 'unregistred'

    id = None

    def __init__(self, id=None, **spec):
        self.id = id
        self.size = spec.pop('size','5G')
        self.state = Volume.REGISTRED

    @classmethod
    def _from_etcd(klass, data):
        id = data.key.split('/')[-1]
        spec = {}
        state = Volume.REGISTRED

        for node in data.children:
            if node.key.split('/')[-1] == 'spec':
                spec = json.loads(node.value)
            if node.key.split('/')[-1] == 'state':
                state = node.value
        v = klass(id, **spec)
        v.state = state
        return v

    def to_json(self):
        return json.dumps({
            'id': self.id,
            'spec': {
                'size': self.size
            },
            'state': self.state
        })

    def __repr__(self):
        return '<Volume: {0}:{1} state={2}>'.format(self.id, self.size,
                                                    self.state)

class VolumeManager:
    def __init__(self, etcd):
        self.etcd = etcd

    def __iter__(self):
        volumes = self.etcd.get("/volumes")
        for result in volumes.children:
            if result.dir:
                yield Volume._from_etcd(self.etcd.read(result.key))

