from gevent import monkey
monkey.patch_all()

from cobalt import Cobalt
from config import config

if __name__ == '__main__':
    Cobalt(config).start()
