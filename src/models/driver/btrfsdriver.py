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

import re
import sh

from numbers import Number
from .driver import Driver


class BTRFSDriver(Driver):
    def __init__(self, base_path):
        self._base_path = base_path
        try:
            self._btrfs = sh.Command('btrfs')
            self._btrfs('quota', 'enable', self._base_path)
        except sh.CommandNotFound as e:
            print(self._err('driver init', e.stderr, e.full_cmd))

    def _get_path(self, id):
        return '{}/{}'.format(self._base_path, id)

    def _get_quota(self, quota):
        return '{}G'.format(quota)

    def _err(self, operation, stderr, cmd):
        return '''BTRFS driver failed!
                OPERATION: {}
                COMMAND: {}
                STDERR: {}'''.format(operation, cmd, stderr)

    def create(self, requirements):
        if not isinstance(requirements['reserved_size'], Number):
            return False
        try:
            self._btrfs('subvolume', 'create', self._get_path(requirements['id']))
            self._set_quota(requirements['id'], requirements['reserved_size'])
        except sh.ErrorReturnCode_1 as e:
            print(self._err('create', e.stderr, e.full_cmd))
            return False

        return True

    def _set_quota(self, id, quota):
        try:
            self._btrfs('qgroup', 'limit', '-e', self._get_quota(quota), self._get_path(id))
        except sh.ErrorReturnCode_1 as e:
            print(self._err('resize', e.stderr, e.full_cmd))
            return False

        return True

    def resize(self, id, quota):
        return self._set_quota(id, quota)

    def clone(self, id, parent_id):
        try:
            self._btrfs('subvolume', 'snapshot', self._get_path(parent_id), self._get_path(id))
        except sh.ErrorReturnCode_1 as e:
            print(self._err('clone', e.stderr, e.full_cmd))
            return False

        return True

    def remove(self, id):
        try:
            self._btrfs('subvolume', 'delete', self._get_path(id))
        except sh.ErrorReturnCode_1 as e:
            print(self._err('remove', e.stderr, e.full_cmd))
            return False

        return True

    def expose(self, id, host, permissions):
        export = '{}   {}({})\n'.format(self._get_path(id), host, ','.join(permissions))
        try:
            with open('/etc/exports', 'a') as f:
                f.write(export)
        except IOError:
            return False

        return True

    def get_all(self):
        ids = []
        try:
            subvolumes = self._btrfs('subvolume', 'list', '-o', self._base_path)
            subvolumes = subvolumes.strip()

            for line in subvolumes.splitlines():
                path = line.strip().split()[-1]

                try:
                    id = None

                    # Seems like output may vary, the path can be absolute or relative
                    # so a check is needed
                    if '/' not in path:
                        id = path
                    elif self._base_path in path:
                        id = path[path.index('{}/'.format(self._base_path)):].replace('{}/'.format(self._base_path), '')

                    if id:
                        ids.append(id)
                except ValueError:
                    pass

        except sh.ErrorReturnCode_1 as e:
            print(self._err('get_all', e.stderr, e.full_cmd))
            return []

        return ids

    """
    Gets info about total disk space and quota groups
    using the usage command provided by btrfs tools

    Unit of measure is GiB
    """
    def get_usage(self):
        try:
            size, qgroups = None, []
            usage = self._btrfs('filesystem', 'usage', '--gbytes', '-h', self._base_path)
            usage = usage.strip()

            match = None
            for line in usage.splitlines():
                if 'Device size:' in line:
                    match = re.search(r'([0-9]+\.[0-9]+)GiB', line)
                    break

            if match:
                size = float(match.group(1))

            for id in self.get_all():
                qgroup = self._btrfs('qgroup', 'show', '-e', '-f', '--gbytes', self._get_path(id))
                qgroup = qgroup.strip()
                match = re.search(r'[0-9]+\.[0-9]+GiB.*[0-9]+\.[0-9]+GiB.*([0-9]+\.[0-9]+)GiB', qgroup)

                if match:
                    qgroups.append(float(match.group(1)))

        except sh.ErrorReturnCode_1 as e:
            print(self._err('get_all', e.stderr, e.full_cmd))

        return size, qgroups
