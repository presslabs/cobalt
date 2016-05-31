import time


class Executor:
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
            volume = self.volume_manager.watch(timeout=self.delay, index=self._watch_index)
            if volume is None:
                self.reset()
                return

            self._watch_index = volume.modifiedIndex + 1

        self._process(volume)

    def _process(self, volume):
        # make check to see if worth working on volume short-circuit

        # machines = self.machine_manager.all()

        # remove machines without labels
        # sort machines by available space

        pass

    def get_active_machine_keys(self):
        _, machines = self.machine_manager.all()
        return [entry.key for entry in machines]

    # TODO test volume_manager watch
    # TODO test executor
    # TODO test engine _machine loop
