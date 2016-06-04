import sh

from driver import Driver


class BTRFSDriver(Driver):
    def __init__(self, base_path):
        self._base_path = base_path

    def _get_path(self, id):
        return '{}/{}'.format(self._base_path, id)

    def _get_quota(self, quota):
        return '{}G'.format(quota)

    def _err(self, operation, stderr, cmd):
        return 'BTRFS driver failed! \nOPERATION: {} \nCOMMAND: {} \nSTDERR: {}'.format(operation, cmd, stderr)

    def create(self, requirements):
        try:
            sh.btrfs.subvolume.create(self._get_path(requirements['id']))
            quota = self._get_quota(requirements['reserved_size'])
            self._set_quota(requirements['id'], quota)
        except sh.ErrorReturnCode_1 as e:
            print(self._err('create', e.stderr, e.full_cmd))
            return False

        return True

    def _set_quota(self, id, quota):
        try:
            sh.btrfs.qgroup.limit(quota, self._get_path(id))
        except sh.ErrorReturnCode_1 as e:
            print(self._err('resize', e.stderr, e.full_cmd))
            return False

        return True

    def resize(self, id, quota):
        self._set_quota(self, id, quota)

    def clone(self, id, parent_id):
        try:
            sh.btrfs.subvolume.snapshot(self._get_path(parent_id), self._get_path(id))
        except sh.ErrorReturnCode_1 as e:
            print(self._err('clone', e.stderr, e.full_cmd))
            return False

        return True

    def remove(self, id):
        try:
            sh.btrfs.subvolume.delete(self._get_path(id))
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
            subvolumes = sh.btrfs.subvolume.list('-o', self._base_path)

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

    # TODO implement accurate disk memory usage info for BTRFS
    def get_free_space(self):
        try:
            pass
        except Exception:
            pass

