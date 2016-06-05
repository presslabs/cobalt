from abc import ABCMeta, abstractmethod


class Driver(metaclass=ABCMeta):
    @abstractmethod
    def create(self, requirements):
        pass

    @abstractmethod
    def resize(self, id, quota):
        pass

    @abstractmethod
    def clone(self, id, parent_id):
        pass

    @abstractmethod
    def remove(self, id):
        pass

    @abstractmethod
    def expose(self, id, host, permissions):
        pass

    @abstractmethod
    def get_all(self):
        pass