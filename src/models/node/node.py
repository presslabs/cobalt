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

from configparser import ConfigParser

from models.driver import BTRFSDriver


class Node:
    """
    # Dummy config example
    [bk1-z3.presslabs.net]
    labels = ssd, some_label, another_label ...
    """
    def __init__(self, context):
        self._conf_path = context['conf_path']
        self._driver = BTRFSDriver(context['volume_path'])
        self._name, self._labels = '', []
        self._available = self.get_space()

        config = ConfigParser()
        config.read(self._conf_path)

        try:
            self._name = config.sections()[0]

            # Rule of thumb: have all labels declared on the same line in config file
            for key, value in config[self._name].items():
                self._labels.extend([label.strip() for label in value.split(',') if key == 'labels'])
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

    def get_space(self):
        total, used = self._driver.df()

        if total and used:
            # Max fill only up to 80%
            total -= total * 0.2
            return total - used

        return None
