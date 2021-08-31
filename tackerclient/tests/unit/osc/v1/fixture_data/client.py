# Copyright 2019 NTT DATA
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import fixtures
from keystoneauth1 import fixture
from keystoneauth1 import loading
from keystoneauth1 import session

from tackerclient.v1_0 import client as proxy_client

IDENTITY_URL = 'http://identityserver:5000/v3'
TACKER_URL = 'http://nfv-orchestration'


class ClientFixture(fixtures.Fixture):

    def __init__(self, requests_mock, identity_url=IDENTITY_URL,
                 api_version='1'):
        super(ClientFixture, self).__init__()
        self.identity_url = identity_url
        self.client = None
        self.token = fixture.V2Token()
        self.token.set_scope()
        self.requests_mock = requests_mock
        self.discovery = fixture.V2Discovery(href=self.identity_url)
        s = self.token.add_service('nfv-orchestration')
        s.add_endpoint(TACKER_URL)
        self.api_version = api_version

    def setUp(self):
        super(ClientFixture, self).setUp()
        auth_url = '%s/tokens' % self.identity_url
        headers = {'X-Content-Type': 'application/json'}
        self.requests_mock.post(auth_url, json=self.token, headers=headers)
        self.requests_mock.get(self.identity_url, json=self.discovery,
                               headers=headers)
        self.client = self.new_client()

    def new_client(self):
        self.session = session.Session()
        loader = loading.get_plugin_loader('password')
        self.session.auth = loader.load_from_options(
            auth_url=self.identity_url, username='xx', password='xx')

        return proxy_client.Client(service_type='nfv-orchestration',
                                   interface='public',
                                   endpoint_type='public',
                                   region_name='RegionOne',
                                   auth_url=self.identity_url,
                                   token=self.token.token_id,
                                   endpoint_url=TACKER_URL,
                                   api_version=self.api_version)
