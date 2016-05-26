import time

from models import Volume


class Executor:
    def __init__(self, volume_manager: Volume, timeout=10):
        self.volume_manager = volume_manager
        self.delay = timeout

    def timeout(self):
        time.sleep(self.delay)

    def tick(self):
        pass
