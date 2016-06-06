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

import json


class Node:
    """
    # Dummy config example
    {
        "name": "bk1-z3.presslabs.net",
        "labels": ["ssd"]
    }
    """
    def __init__(self, context, driver):
        self._conf_path = context['conf_path']
        self._conf = context['conf']
        self._driver = driver
        self._available = self.get_space()
        self._max_fill = context['max_fill']

        try:
            if len(self._conf['name']) and len(self._conf['labels']):
                with open(self._conf_path, 'w') as c:
                    json.dump(self._conf, c)
            else:
                with open(self._conf_path, 'r') as c:
                    self._conf = json.load(c)
        except (IOError, ValueError):
            pass

    def get_subvolumes(self):
        return self._driver.get_all()

    @property
    def name(self):
        return self._conf['name']

    @property
    def labels(self):
        return self._conf['labels']

    def get_space(self):
        total, used = self._driver.df()

        if total and used:
            total -= total * (1 - self._max_fill)
            return total - used

        return None
