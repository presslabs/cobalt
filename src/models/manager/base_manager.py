# Copyright 2016 Presslabs SRL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import etcd
from flask import json
from marshmallow import Schema


class BaseManager:
    """Base repository class for objects"""

    KEY = ''
    """Directory name in ETCD"""

    def __init__(self, client):
        """Create an instance of the repository with the specified source

        Args:
            client (etcd.Client): The data source for the repository
        """
        self.client = client

        try:
            self.client.write(self.KEY, '', dir=True)
        except (etcd.EtcdAlreadyExist, etcd.EtcdNotFile):
            pass

    def all(self):
        """Get all objects maintained by this repository

        Returns:
            tuple:
                0 etcd.Result: The directory object **NOT expanded**
                1 [etcd.Result] List of The objects with expanded values
        """
        try:
            dir = self.client.read(self.KEY, sorted=True)
            entries = [entry for entry in dir.leaves if not entry.dir]
        except etcd.EtcdKeyNotFound:
            dir = None
            entries = []

        return dir, self._load_from_etcd(entries)

    def all_keys(self):
        """Get all object keys maintained by this repository

        Returns:
            [str]: A list of key strings
        """
        return [entry.key for entry in self.all()[1]]

    def by_id(self, entry_id):
        """Get the object referenced by id

        Args:
            entry_id (str): The id to fetch prefixed with the object dir

        Returns:
            etcd.Result: The expanded result if key exists, or None if key not found
        """
        try:
            entry = self.client.read('/{}/{}'.format(self.KEY, entry_id))
        except etcd.EtcdKeyNotFound:
            return None

        return self._load_from_etcd(entry)

    def create(self, data, suffix=''):
        """Create a new object inside the data store

        Args:
            data (dict): Dictionary containing values you want to store
            suffix (str): If given then it will be used as a key while storing

        Returns:
            etcd.Result: THe created object expanded
        """
        append = True if suffix == '' else False
        key = '/{}/{}'.format(self.KEY, suffix)

        entry = self.client.write(key, json.dumps(data), append=append)

        return self._load_from_etcd(entry)

    def update(self, entity):
        """Update an existing object from the data store

        Args:
            entity (etcd.Result): An expanded result object that needs to be serialized

        Returns:
            etcd.Result: The resulting object expanded, or None if Etcd failed
        """
        entity.value = json.dumps(entity.value)

        try:
            entity = self.client.update(entity)
        except (etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound):
            return None

        return self._load_from_etcd(entity)

    def delete(self, entity):
        """Delete an object from the data store

        Args:
            entity (etcd.Result): The object one wants to be deleted, expanded or not

        Returns:
            etcd.Result: The result of the operation expanded, or None if etcd failed
        """
        try:
            entity = self.client.delete(entity.key)
        except (etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound):
            return None

        return self._load_from_etcd(entity)

    def watch(self, index=None, timeout=0):
        """Watch the directory of the repository for changes indefinably starting from an index

        Args:
            index (int): The index to start watching from
            timeout (int): The timeout after which we give up

        Returns:
            etcd.Result: Result expanded or None if timeout occurred
        """
        try:
            entity = self.client.watch(self.KEY, recursive=True, index=index, timeout=timeout)
        except etcd.EtcdWatchTimedOut:
            return None
        return self._load_from_etcd(entity)

    def get_id_from_key(self, key):
        """Utility method for getting the id from an internal key

        Args:
            key (str): THe objects key

        Returns:
            str: The respective id
        """
        return key[len(self.KEY) + 2:]

    def _load_from_etcd(self, data):
        """Utility method to expand result objects

        Args:
            data ([etcd.result] | etcd.result): The iterable or a single result object not expanded

        Returns:
             etcd.result: Return type matches given input (if it is a list->list), and all result objects are expanded
        """
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
