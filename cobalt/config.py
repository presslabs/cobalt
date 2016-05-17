from collections import ChainMap

from config import config
from utils.read_only_dict import ReadOnlyDict

_defaults = {
    'etcd': {
        # python-etcd client parameters https://github.com/jplana/python-etcd/blob/master/src/etcd/client.py
        'host': '127.0.0.1',
        'port': 4001,
        'srv_domain': None,
        'version_prefix': '/v2',
        'read_timeout': 60,
        'allow_redirect': True,
        'protocol': 'http',
        'cert': None,
        'ca_cert': None,
        'username': None,
        'password': None,
        'allow_reconnect': False,
        'use_proxies': False,
        'expected_cluster_id': None,
        'per_host_pool_size': 10
    },
    'engine': {
        'lease_ttl': 60,
        'refresh_ttl': 40
    },
    'api': {
        'host': '',
        'port': 5000
    },
    'services': ['engine', 'api', 'agent'],
    'mount_point': None
}


def generate_context(defaults, user):
    return ReadOnlyDict(ChainMap(user, defaults))

context = generate_context(_defaults, config)
