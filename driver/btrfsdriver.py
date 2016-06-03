import sh

from .driver import Driver
from time import time


class BTRFSDriver(Driver):
    def __init__(self, path):
        self._path = path

    def create(self, requirements):
        try:
            sh.btrfs.subvolume.create('{}/{}'.format(self._path, requirements['id']))
            quota = '{}G'.format(requirements['reserved_size'])

            self._set_quota(requirements['id'], quota)
        except sh.ErrorReturnCode_1 as e:
            print(e.message, e.full_cmd)
            return False

        return True

    def _set_quota(self, id, quota):
        try:
            sh.btrfs.qgroup.limit(quota, '{}/{}'.format(self._path, id))
        except sh.ErrorReturnCode_1 as e:
            print(e.message, e.full_cmd)
            return False

        return True

    def resize(self, id, quota):
        self._set_quota(self, id, quota)

    def clone(self, id):
        try:
            sh.btrfs.subvolume.snapshot('{}/{}'.format(self._path, id), '{}/clone-{}-{}'.format(self._path, id, time.strftime('%d%m%Y%H%M%S')))
        except sh.ErrorReturnCode_1 as e:
            print(e.message, e.full_cmd)
            return False

        return True

    def remove(self, id):
        try:
            sh.btrfs.subvolume.delete('{}/{}'.format(self._path, id))
        except sh.ErrorReturnCode_1 as e:
            print(e.message, e.full_cmd)
            return False

        return True

    def expose(self, id, host, permissions):
        export = '{}/{}   {}({})\n'.format(self._path, id, host, ','.join(permissions))
        try:
            with open('/etc/exports', 'a') as f:
                f.write(export)
        except IOError:
            return False

        return True

    def get_all(self):
        ids = []
        try:
            subvolumes = sh.btrfs.subvolume.list('-o', self._path)
            for line in subvolumes:
                line = line.strip()
                id = int(line[line.index('{}/').format(self._path):].replace('{}/'.format(self._path), ''))
                ids.append(id)
        except sh.ErrorReturnCode_1 as e:
            print(e.message, e.full_cmd)
            return False
        return ids
