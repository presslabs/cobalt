import sh

from .driver import Driver


class BTRFSDriver(Driver):
    def __init__(self, path):
        self._path = path

    def create(self, requirements):
        try:
            sh.btrfs.subvolume.create('{}/{}'.format(self._path, requirements['id']))
            quota = '{}G'.format(requirements['requested']['reservedSize'])

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
            sh.btrfs.subvolume.snapshot('{}/{}'.format(self._path, id), '{}/clone-{}'.format(self._path, id))
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

