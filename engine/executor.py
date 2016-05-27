import time


class Executor:
    def __init__(self, volume_manager, context):
        self.volume_manager = volume_manager
        self.delay = 10
        try:
            self.delay = int(context['timeout'])
        except (KeyError, ValueError) as e:
            print('Context provided to Executor erroneous: {}, defaulting: {}\n{}'.format(context, self.delay, e))

    def timeout(self):
        time.sleep(self.delay)

    def tick(self):
        pass

    def reset(self):
        pass
