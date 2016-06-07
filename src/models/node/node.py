# Copyright 2016 PressLabs SRL
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

from configparser import ConfigParser

from models.driver import BTRFSDriver


class Node:
    """
    # Dummy config example
    [bk1-z3.presslabs.net]
    ssd = True
    """
    def __init__(self, context):
        self._conf_path = context['conf_path']
        self._driver = BTRFSDriver(context['volume_path'])
        self._name, self._labels = '', {}

        config = ConfigParser()
        config.read(self._conf_path)

        try:
            self._name = config.sections()[0]
            for label, value in config[self._name].iteritems():
                self._labels[label] = value
        except IndexError:
            pass

    def get_subvolumes(self):
        return self._driver.get_all()

    @property
    def name(self):
        return self._name

    @property
    def labels(self):
        return self._labels

