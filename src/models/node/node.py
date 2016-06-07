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

from models.driver import BTRFSDriver


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
        self._driver = driver
        self._max_fill = context['max_fill']
        self._available = self.get_space()

        try:
            with open(self._conf_path, 'r') as c:
                self._conf = json.load(c)
            if self._conf != context['conf']:
                warning_msg = """
                    WARNING: Configurations found in {0} differ from the configurations provided inside cobalt config!\n
                    Defaulting to configurations from {0}, if these configurations are wrong, then remove the {0} file.
                """.format(self._conf_path).strip()
                print(warning_msg)
        except (IOError, FileNotFoundError, PermissionError, ValueError):
            warning_msg = """
                WARNING: Configuration file {0} doesn't exist or its contents are not in the correct format. Trying to
                write Cobalt provided configurations into it.
            """.format(self._conf_path).strip()
            print(warning_msg)

            self._conf = context['conf']

            try:
                with open(self._conf_path, 'w') as c:
                    json.dump(self._conf, c)
            except PermissionError:
                warning_msg = 'WARNING: Could not write to {0}'.format(self._conf_path)
                print(warning_msg)

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

