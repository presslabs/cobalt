import time

from models import Volume


class Executor:
    def __init__(self, volume_manager: Volume, timeout=10):
        self.volume_manager = volume_manager
        self.timeout = timeout

    def timeout(self):
        time.sleep(self.timeout)

    def tick(self):
        pass
