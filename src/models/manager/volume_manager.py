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
from marshmallow import fields, Schema, validate, utils

from .base_manager import BaseManager
from time import time


class VolumeAttributeSchema(Schema):
    """Marshmallow schema for the requested subsection"""

    class Meta:
        ordered = True

    reserved_size = fields.Integer(required=True, validate=[validate.Range(min=0)])
    constraints = fields.List(fields.String(validate=[validate.Length(min=1)]), required=True)


class VolumeControlSchema(Schema):
    """Marshmallow schema for the control subsection"""

    class Meta:
        ordered = True

    error = fields.String(default='', missing='')
    error_count = fields.Integer(default=0, missing=0)
    parent_id = fields.String(default='', missing='')


class VolumeSchema(Schema):
    """marshmallow schema for the entire object"""

    class Meta:
        ordered = True

    id = fields.String(required=True)
    state = fields.String(default='scheduling', missing='scheduling')
    name = fields.String(default='', missing='')
    node = fields.String(default='', missing='')

    meta = fields.Dict(default={}, missing={})

    actual = fields.Nested(VolumeAttributeSchema, missing={}, default={})
    requested = fields.Nested(VolumeAttributeSchema, required=True)
    control = fields.Nested(VolumeControlSchema, required=True)

    def get_attribute(self, attr, obj, default):
        """Utility method for getting the id for the representation"""
        if attr == 'id':
            return VolumeManager.get_id_from_key(obj.key)
        return utils.get_value(attr, obj.value, default)


class VolumeManager(BaseManager):
    """Volume repository class"""

    KEY = 'volumes'
    """Directory name in ETCD"""

    def by_states(self, states=None):
        """Returns all volumes that have the state provided

        Args:
            states ([str]): A list of interested states

        Returns:
            [etcd.Result]: A list of expanded results
        """
        volumes = self.all()[1]
        return VolumeManager.filter_states(volumes, states)

    def by_node(self, node):
        """Returns all volumes that have the node provided

        Args:
            node (str): The node you are interested in

        Returns:
             [etcd.Result]: A list of expanded results
        """
        return [volume for volume in self.all() if volume.value['node'] == node]

    def update(self, volume):
        """Similar to what the base manager does only that it updates a volumes updated timestamp"""
        volume.value['control']['updated'] = time()
        volume = super(VolumeManager, self).update(volume)

        if not volume:
            return None

        return volume

    def create(self, data, *unused):
        """Similar to what the base manager does only that it adds the updated timestamp"""
        data['control']['updated'] = time()
        volume = super(VolumeManager, self).create(data, '')

        return volume

    def get_lock(self, id, purpose='clone'):
        """Utility method to get a Lock instance for a specific purpose and a related object id

        Args:
            id (str): The id for which resource it should focus on
            purpose (str): The operation that needs locking

        Returns:
            etcd.Lock: The respective Lock object unarmed
        """
        return etcd.Lock(self.client, '{}-{}'.format(purpose, id))

    @staticmethod
    def get_id_from_key(key):
        """Utility method for getting the id from an internal key

        Args:
            key (str): THe objects key

        Returns:
            str: The respective id
        """
        return key[len(VolumeManager.KEY) + 2:]

    @staticmethod
    def filter_states(volumes, states):
        """Utility method for filtering a list of volume results by state

        Args:
            volumes ([etcd.Result]): The objects that should get filtered
            states ([str]): A list of interested in states

        Returns:
            [etcd.Result]: Returns only the matching objects
        """
        states = states or []
        states = [states] if not isinstance(states, list) else states

        return [volume for volume in volumes if volume.value['state'] in states]
