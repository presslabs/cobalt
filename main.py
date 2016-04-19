#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ft=python:sw=4:ts=4:sts=4:et:
import json
import os
import random
import time

import etcd
import gevent

from gevent.monkey import patch_all
from gevent.queue import Queue
from gevent.pywsgi import WSGIServer

from app import create_api_server
from volume import Volume, VolumeManager

tasks = Queue()
PID = os.getpid()
LEASE_TTL = 3

class Engine:
    def __init__(self, id=None):
        if id is None:
            id = '%d-%d' % (os.getpid(), random.randint(1,99999))
        self.id = id
        self.has_lease = False
        self.etcd = etcd.Client(host='192.168.99.100')
        self.lease = etcd.Lock(self.etcd, 'engine-lock')
        self.volumes = VolumeManager(self.etcd)

    def run(self):
        lease_acquirer = gevent.spawn(self.lease_acquirer)
        schedule_loop = gevent.spawn(self.schedule_loop)
        api_server = WSGIServer(('', 5000), 
                                create_api_server(self.volumes))
        api_server.serve_forever()

    def lease_acquirer(self):
        while True:
            try:
                self.etcd.write('/engine-lease', self.id, ttl=LEASE_TTL,
                                prevExist=False)
                print '{0} acquired lease'.format(self.id)
                self.has_lease = True
            except etcd.EtcdAlreadyExist as e:
                lease_owner = self.etcd.get('/engine-lease')
                if lease_owner.value != self.id:
                    print ('Lease is already owned '
                           'by {0}'.format(lease_owner.value))
                    self.has_lease = False
                else:
                    try:
                        self.etcd.write('/engine-lease', self.id, ttl=LEASE_TTL,
                                        prevIndex=lease_owner.modifiedIndex)
                        print 'Lease extended'
                        self.has_lease = True
                    except etcd.EtcdCompareFailed:
                        print 'Lease lost'
                        self.has_lease = False

            time.sleep(2 * LEASE_TTL / 3)

    def schedule_loop(self):
        while True:
            time.sleep(0)
            if self.has_lease:
                pass

def run():
    patch_all()

    e = Engine()
    e.run()

if __name__ == '__main__':
    run()
