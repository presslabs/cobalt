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
from gevent import monkey
monkey.patch_all()

import json

from sys import argv
from cobalt import Cobalt


def start():
    if len(argv) != 2:
        print('Config file must be specified. Usage: main.py <config_path>')

    try:
        with open(argv[1]) as data_file:
            config = json.load(data_file)
            Cobalt(config).start()
    except Exception as e:
        print('Error encountered when reading config: {}'.format(e))

if __name__ == '__main__':
    start()
