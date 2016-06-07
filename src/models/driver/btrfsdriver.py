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

from .driver import Driver


class BTRFSDriver(Driver):
    def __init__(self, base_path):
        self._base_path = base_path
        try:
            self._btrfs = sh.Command('btrfs')
        except sh.CommandNotFound as e:
            print(self._err('driver init', e.stderr, e.full_cmd))

    def _get_path(self, id):
        return '{}/{}'.format(self._base_path, id)

    def _get_quota(self, quota):
        return '{}G'.format(quota)

    def _err(self, operation, stderr, cmd):
        return 'BTRFS driver failed! \nOPERATION: {} \nCOMMAND: {} \nSTDERR: {}'.format(operation, cmd, stderr)

    def create(self, requirements):
        try:
            self._btrfs('subvolume', 'create', self._get_path(requirements['id']))
            quota = self._get_quota(requirements['reserved_size'])
            self._set_quota(requirements['id'], quota)
        except sh.ErrorReturnCode_1 as e:
            print(self._err('create', e.stderr, e.full_cmd))
            return False

        return True

    def _set_quota(self, id, quota):
        try:
            self._btrfs('qgroup', 'limit', quota, self._get_path(id))
        except sh.ErrorReturnCode_1 as e:
            print(self._err('resize', e.stderr, e.full_cmd))
            return False

        return True

    def resize(self, id, quota):
        self._set_quota(self, id, quota)

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
                line = line.strip()
                try:
                    id = line[line.index('{}/'.format(self._base_path)):].replace('{}/'.format(self._base_path), '')
                    ids.append(int(id))
                except ValueError:
                    pass
        except sh.ErrorReturnCode_1 as e:
            print(self._err('get_all', e.stderr, e.full_cmd))
            return []

        return ids

    """
    Gets info about total disk space and used disk space
    using the df command provided by btrfs tools

    Unit of measure is GiB
    """
    def df(self):
        try:
            usage = self._btrfs('filesystem', 'df', '-g', self._base_path)
            total, used = None, None
            usage = usage.strip()

            # First line should contain overall usage info
            total_usage = usage.splitlines()[0]
            match = re.search(r'total=(.*?)GiB, used=(.*?)GiB', total_usage)

            if match:
                total, used = float(match.group(1)), float(match.group(2))

        except sh.ErrorReturnCode_1 as e:
            print(self._err('get_all', e.stderr, e.full_cmd))

        return total, used
