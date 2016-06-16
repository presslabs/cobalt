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

import time


class Executor:
    """Class responsible for all decision making within the cluster"""

    states_interested_in = ['registered', 'scheduling', 'pending']

    def __init__(self, volume_manager, machine_manager, context):
        """Creates an Executor instance

        Args:
            volume_manager (VolumeManager): Data source for the volume model
            machine_manager (MachineManager): Data source for the machine model
            context (dict): THe context for the Executor
        """
        self.volume_manager = volume_manager
        self.machine_manager = machine_manager

        self.delay = 10
        try:
            self.delay = float(context['timeout'])
        except (KeyError, ValueError) as e:
            print('Context provided to Executor'
                  ' erroneous: {}, defaulting: {}\n{}'.format(context, self.delay, e))

        self._should_reset = True
        self._volumes_to_process = []
        self._watch_index = None

    def timeout(self):
        """Make the Executor sleep for the defined amount, configured inside context"""
        time.sleep(self.delay)

    def reset(self):
        """Reset the state of the Executor causing the next operation to pool and heal"""
        self._should_reset = True
        self._watch_index = None

    def tick(self):
        """Method that causes the Executor to process one volume, either by watching or by polled state"""
        if self._should_reset:
            directory, self._volumes_to_process = self.volume_manager.all()

            self._should_reset = False
            if directory is not None:
                self._watch_index = directory.etcd_index + 1

        if self._volumes_to_process:
            volume = self._volumes_to_process.pop()
        else:
            volume = self.volume_manager.watch(timeout=self.delay, index=self._watch_index)
            if volume is None:
                self.reset()
                return

            self._watch_index = volume.modifiedIndex + 1
            if volume.action == 'expire' or volume.action == 'delete':
                return

        self._process(volume)

    def _process(self, volume):
        """Method for processing a volume

        It figures out the next state and tries to transition the object based on the
        state machine diagram

        Args:
            volume (etcd.Result): THe volume object to process
        """
        in_state = self.volume_manager.filter_states([volume], self.states_interested_in)
        if not in_state:
            return

        state = volume.value['state']
        if state == 'scheduling':
            self._process_scheduling(volume)
        elif state == 'pending':
            self._process_pending(volume)

    def _process_scheduling(self, volume):
        """Process scheduling volume

        Apply the scheduling transition or healing.

        Args:
            volume (etcd.Result): An expanded version
        """
        value = volume.value
        last_updated = value['control']['updated']
        expired = True if time.time() - last_updated > self.delay else False

        if not value['node'] or expired:
            machine = self._find_machine(volume)
            if not machine:
                return

            value['node'] = machine.value['name']
        else:
            return

        self.volume_manager.update(volume)

    def _process_pending(self, volume):
        """Process pending volume

        Apply the pending transition.

        Args:
            volume (etcd.Result): An expanded version
        """
        value = volume.value
        value['state'] = self._next_state(volume)

        if value['state'] == 'cloning':
            self._process_cloning(volume)
        else:
            self.volume_manager.update(volume)

    def _process_cloning(self, volume):
        """Process cloning volume

        Apply the cloning transition.

        Args:
            volume (etcd.Result): An expanded version
        """
        value = volume.value
        parent = self.volume_manager.by_id(value['control']['parent_id'])

        if not parent:
            value['state'] = 'deleting'
        else:
            value['node'] = parent.value['node']

        self.volume_manager.update(volume)

    def _find_machine(self, volume):
        """Utility method to get an appropriate machine for a volume, based on required space and constraints

        Args:
            volume (etcd.Result): The volume it should find place for

        Returns:
            etcd.Result: The matched machine with expanded value
        """
        constraints = volume.value['requested']['constraints']
        machines = self.machine_manager.all()[1]

        machines_ok = []
        for machine in machines:
            labels = machine.value['labels']
            if not all(x in labels for x in constraints):
                continue

            requested_size = volume.value['requested']['reserved_size']
            if machine.value['available'] < requested_size:
                continue

            machines_ok.append(machine)

        if not machines_ok:
            return

        machines_ok.sort(key=lambda x: x.value['available'], reverse=True)
        return machines_ok[0]

    def _next_state(self, volume):
        """Utility method for finding the next state of a volume based on transitions available

        Args:
            volume (etcd.Result): And expanded volume representation

        Returns:
            str: Next state
        """
        value = volume.value

        if value['control']['parent_id']:
            return 'cloning'

        if value['requested'] == value['actual']:
            return 'ready'

        actual_size = value['actual']['reserved_size']
        requested_size = value['requested']['reserved_size']
        if requested_size != actual_size:
            return 'resizing'

        print('Next state for volume {} can\'t be determined!'.format(volume))
        return 'error'
