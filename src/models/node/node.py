from configparser import ConfigParser

from models.driver import BTRFSDriver


class Node:
    """
    # Dummy config example
    [bk1-z3.presslabs.net]
    ssd = True
    """
    def __init__(self, context):
        self._conf_path = context['conf_path']
        self._driver = BTRFSDriver(context['volume_path'])
        self._name, self._labels = '', {}

        config = ConfigParser()
        config.read(self._conf_path)

        try:
            self._name = config.sections()[0]
            for label, value in config[self._name].iteritems():
                self._labels[label] = value
        except IndexError:
            pass

    def get_subvolumes(self):
        return self._driver.get_all()

    @property
    def name(self):
        return self._name

    @property
    def labels(self):
        return self._labels

