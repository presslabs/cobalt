import time
import etcd


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
            self._volumes_to_process = self.volume_manager.all()

        if self._volumes_to_process:
            volume = self._volumes_to_process.pop()
        else:
            try:
                volume = self.volume_manager.watch(timeout=self.delay, index=self._watch_index)

                # watch may cause a context switch, a reset may have happened
                if self._watch_index is not None:
                    self._watch_index = volume.modifiedIndex + 1
            except etcd.EtcdWatchTimedOut:
                self.reset()
                return

        self._process(volume)

    def _process(self, volume):
        # make check to see if worth working on volume short-circuit

        # machines = self.machine_manager.all()

        # remove machines without labels
        # sort machines by available space

        pass

    def get_active_machine_keys(self):
        return [entry.key for entry in self.machine_manager.all()]

    # TODO test volume_manager watch
    # TODO test executor
    # TODO test engine _machine loop
