from abc import ABCMeta, abstractmethod


class Driver(metaclass=ABCMeta):
    @abstractmethod
    def create(self, requirements):
        pass

    @abstractmethod
    def _set_quota(self, id, quota):
        pass

    @abstractmethod
    def resize(self, id, quota):
        pass

    @abstractmethod
    def clone(self, id):
        pass

    @abstractmethod
    def remove(self, id):
        pass

    @abstractmethod
    def expose(self, id, host, permissions):
        pass
