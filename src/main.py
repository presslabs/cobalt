from gevent import monkey
monkey.patch_all()

from cobalt import cobalt

if __name__ == '__main__':
    cobalt.start()
