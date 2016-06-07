# Copyright 2016 Presslabs SRL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

config = {
    'etcd': {
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
        'per_host_pool_size': 10,
    },
    'engine': {
        'leaser': {
            'lease_ttl': 60,
            'refresh_ttl': 40,
        },
        'executor': {
            'timeout': 10
        }
    },
    'api': {
        'host': '',
        'port': 5000
    },
    'agent': {
        'agent_ttl': 60,
        'max_error_count': 3,
        'node': {
            'volume_path': '/volumes',
            'conf_path': '/etc/cobalt.conf'
        },
        'watch_timeout': 10
    },
    'services': ['api', 'engine', 'agent'],
    'mount_point': None
}
