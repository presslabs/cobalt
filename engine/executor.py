import time


class Executor:
    states_interested_in = ['registered', 'scheduling', 'pending']

    def __init__(self, volume_manager, machine_manager, context):
        self.volume_manager = volume_manager
        self.machine_manager = machine_manager

        self.delay = 10
        try:
            self.delay = int(context['timeout'])
        except (KeyError, ValueError) as e:
            print('Context provided to Executor erroneous: {}, defaulting: {}\n{}'.format(context, self.delay, e))

        self._should_reset = True
        self._volumes_to_process = []
        self._watch_index = None

    def timeout(self):
        time.sleep(self.delay)

    def reset(self):
        self._should_reset = True
        self._watch_index = None

    def tick(self):
        if self._should_reset:
            directory, self._volumes_to_process = self.volume_manager.all()

            if directory is not None:
                self._watch_index = directory.etcd_index

        if self._volumes_to_process:
            volume = self._volumes_to_process.pop()
        else:
            # TODO expose timeout here as an extra config
            volume = self.volume_manager.watch(timeout=self.delay, index=self._watch_index)
            if volume is None:
                self.reset()
                return

            self._watch_index = volume.modifiedIndex + 1
            if volume.action == 'expire' or volume.action == 'delete':
                return

        self._process(volume)

    def _process(self, volume):
        in_state = self.volume_manager.filter_states([volume], self.states_interested_in)
        if not in_state:
            return

        data = volume.value
        state = data['state']
        node = data['node']

        # TODO expose expired timeout in config
        expired = True if time.time() - data['control']['updated'] > self.delay else False

        if state == 'scheduling':
            if not node or expired:
                machine = self._find_machine(volume)
                if not machine:
                    return

                data['node'] = machine.value['name']
        elif state == 'pending':
            if data['requested'] == data['actual']:
                data['state'] = 'ready'
            else:
                next_state = self._next_state(volume)
                if not next_state:
                    return

                data['state'] = next_state
                if next_state == 'cloning':
                    parent = self.volume_manager.by_id(data['control']['parent_id'])
                    data['node'] = parent.value['node']

        self.volume_manager.update(volume)

    # TODO test volume_manager watch
    # TODO test executor
    # TODO test engine _machine loop
    # TODO test api delete when clones exist

    def _find_machine(self, volume):
        constraints = volume.value['requested']['contraints']
        machines = self.machine_manager.all()[1]

        machines_ok = []
        for machine in machines:
            labels = machine.value['labels']
            if not all(x in labels for x in constraints):
                continue

            if machine.value['available'] < volume.value['requested']['reserved_size']:
                continue

            machines_ok.append(machine)

        if not machines_ok:
            return

        machines_ok.sort(key=lambda x: x.value['available'], reverse=True)
        return machines_ok[0]

    def _next_state(self, volume):
        value = volume.value

        if value['control']['parent_id']:
            return 'cloning'

        if value['requested']['reserved_size'] != volume['actual']['reserved_size']:
            return 'resizing'

        print('Next state for volume {} can\'t be determined!'.format(volume))
        return
