# Copyright (C) 2013 OpenStack Foundation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from unittest import mock

import fixtures
from keystoneclient import session
import requests
import testtools

from tackerclient import client
from tackerclient.common import clientmanager
from tackerclient.common import exceptions
from tackerclient import shell as openstack_shell


AUTH_TOKEN = 'test_token'
END_URL = 'test_url'
METHOD = 'GET'
URL = 'http://test.test:1234/v1.0/'
CA_CERT = '/tmp/test/path'
DEFAULT_API_VERSION = '1.0'


class TestSSL(testtools.TestCase):
    def setUp(self):
        super(TestSSL, self).setUp()

        self.useFixture(fixtures.EnvironmentVariable('OS_TOKEN', AUTH_TOKEN))
        self.useFixture(fixtures.EnvironmentVariable('OS_URL', END_URL))
        self.addCleanup(mock.patch.stopall)

    def _test_verify_client_manager(self, cacert):
        with mock.patch.object(session, 'Session'), \
                mock.patch.object(clientmanager, 'ClientManager') as mock_cmgr:

            mock_cmgr.return_value = 0
            shell = openstack_shell.TackerShell(DEFAULT_API_VERSION)
            shell.options = mock.Mock()
            auth_session = shell._get_keystone_session()

            shell.run(cacert)

        mock_cmgr.assert_called_with(
            api_version={'nfv-orchestration': '1.0'},
            auth=auth_session.auth, auth_strategy='keystone',
            auth_url='', ca_cert=CA_CERT, endpoint_type='publicURL',
            insecure=False, log_credentials=True, password='',
            raise_errors=False, region_name='', retries=0,
            service_type='nfv-orchestration', session=auth_session,
            tenant_id='', tenant_name='', timeout=None,
            token='test_token', url='test_url', user_id='', username='')

    def test_ca_cert_passed(self):
        cacert = ['--os-cacert', CA_CERT]
        self._test_verify_client_manager(cacert)

    def test_ca_cert_passed_as_env_var(self):
        self.useFixture(fixtures.EnvironmentVariable('OS_CACERT', CA_CERT))
        self._test_verify_client_manager([])

    @mock.patch.object(client.HTTPClient, 'request')
    def test_proper_exception_is_raised_when_cert_validation_fails(self,
                                                                   mock_req):
        http = client.HTTPClient(token=AUTH_TOKEN, endpoint_url=END_URL)
        mock_req.side_effect = requests.exceptions.SSLError()
        self.assertRaises(
            exceptions.SslCertificateValidationError,
            http._cs_request,
            URL, METHOD
        )
