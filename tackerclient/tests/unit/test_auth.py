# Copyright 2012 NEC Corporation
# All Rights Reserved
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
#

import copy
import json
from unittest import mock
import uuid

from keystoneclient import exceptions as k_exceptions
import requests
import testtools

from tackerclient import client
from tackerclient.common import exceptions


USERNAME = 'testuser'
USER_ID = 'testuser_id'
TENANT_NAME = 'testtenant'
TENANT_ID = 'testtenant_id'
PASSWORD = 'password'
AUTH_URL = 'authurl'
ENDPOINT_URL = 'localurl'
ENDPOINT_OVERRIDE = 'otherurl'
TOKEN = 'tokentoken'
REGION = 'RegionTest'
NOAUTH = 'noauth'

KS_TOKEN_RESULT = {
    'access': {
        'token': {'id': TOKEN,
                  'expires': '2012-08-11T07:49:01Z',
                  'tenant': {'id': str(uuid.uuid1())}},
        'user': {'id': str(uuid.uuid1())},
        'serviceCatalog': [
            {'endpoints_links': [],
             'endpoints': [{'adminURL': ENDPOINT_URL,
                            'internalURL': ENDPOINT_URL,
                            'publicURL': ENDPOINT_URL,
                            'region': REGION}],
             'type': 'nfv-orchestration',
             'name': 'Tacker Service'}
        ]
    }
}

ENDPOINTS_RESULT = {
    'endpoints': [{
        'type': 'nfv-orchestration',
        'name': 'Tacker Service',
        'region': REGION,
        'adminURL': ENDPOINT_URL,
        'internalURL': ENDPOINT_URL,
        'publicURL': ENDPOINT_URL
    }]
}


def get_response(status_code, headers=None):
    response = mock.Mock().CreateMock(requests.Response)
    response.headers = headers or {}
    response.status_code = status_code
    return response


resp_200 = get_response(200)
resp_401 = get_response(401)
headers = {'X-Auth-Token': '',
           'User-Agent': 'python-tackerclient'}
expected_headers = {'X-Auth-Token': TOKEN,
                    'User-Agent': 'python-tackerclient'}
agent_header = {'User-Agent': 'python-tackerclient'}


class CLITestAuthNoAuth(testtools.TestCase):

    def setUp(self):
        """Prepare the test environment."""
        super(CLITestAuthNoAuth, self).setUp()
        self.client = client.HTTPClient(username=USERNAME,
                                        tenant_name=TENANT_NAME,
                                        password=PASSWORD,
                                        endpoint_url=ENDPOINT_URL,
                                        auth_strategy=NOAUTH,
                                        region_name=REGION)
        self.addCleanup(mock.patch.stopall)

    @mock.patch('tackerclient.client.HTTPClient.request')
    def test_get_noauth(self, mock_request):

        mock_request.return_value = (resp_200, '')
        self.client.do_request('/resource', 'GET',
                               headers=headers)
        mock_request.assert_called_once_with(
            ENDPOINT_URL + '/resource',
            'GET',
            headers=headers,
            content_type=None)
        self.assertEqual(self.client.endpoint_url, ENDPOINT_URL)


class CLITestAuthKeystone(testtools.TestCase):

    # Auth Body expected
    auth_body = ('{"auth": {"tenantName": "testtenant", '
                 '"passwordCredentials": '
                 '{"username": "testuser", "password": "password"}}}')

    def setUp(self):
        """Prepare the test environment."""
        super(CLITestAuthKeystone, self).setUp()
        self.client = client.HTTPClient(username=USERNAME,
                                        tenant_name=TENANT_NAME,
                                        password=PASSWORD,
                                        auth_url=AUTH_URL,
                                        region_name=REGION)
        self.addCleanup(mock.patch.stopall)

    def test_reused_token_get_auth_info(self):
        """Test Client.get_auth_info().

        Test that Client.get_auth_info() works even if client was
        instantiated with predefined token.
        """
        client_ = client.HTTPClient(username=USERNAME,
                                    tenant_name=TENANT_NAME,
                                    token=TOKEN,
                                    password=PASSWORD,
                                    auth_url=AUTH_URL,
                                    region_name=REGION)
        expected = {'auth_token': TOKEN,
                    'auth_tenant_id': None,
                    'auth_user_id': None,
                    'endpoint_url': self.client.endpoint_url}
        self.assertEqual(client_.get_auth_info(), expected)

    @mock.patch('tackerclient.client.HTTPClient.request')
    def test_get_token(self, mock_request):

        mock_request.return_value = (resp_200, json.dumps(KS_TOKEN_RESULT))
        self.client.do_request('/resource', 'GET')
        mock_request.assert_called_with(
            ENDPOINT_URL + '/resource', 'GET',
            headers=expected_headers, content_type=None)
        self.assertEqual(self.client.endpoint_url, ENDPOINT_URL)
        self.assertEqual(self.client.auth_token, TOKEN)

    @mock.patch('tackerclient.client.HTTPClient.request')
    def test_refresh_token(self, mock_request):

        self.client.auth_token = TOKEN
        self.client.endpoint_url = ENDPOINT_URL

        # If a token is expired, tacker server returns 401
        mock_request.return_value = (resp_401, '')
        self.assertRaises(exceptions.Unauthorized,
                          self.client.do_request,
                          '/resource',
                          'GET')

        mock_request.return_value = (resp_200, json.dumps(KS_TOKEN_RESULT))
        self.client.do_request('/resource', 'GET')
        mock_request.assert_called_with(
            ENDPOINT_URL + '/resource', 'GET',
            headers=expected_headers, content_type=None)

    @mock.patch('tackerclient.client.HTTPClient.request')
    def test_refresh_token_no_auth_url(self, mock_request):

        self.client.auth_url = None

        self.client.auth_token = TOKEN
        self.client.endpoint_url = ENDPOINT_URL

        # If a token is expired, tacker server returns 401
        mock_request.return_value = (resp_401, '')
        self.assertRaises(exceptions.NoAuthURLProvided,
                          self.client.do_request,
                          '/resource',
                          'GET')
        expected_url = ENDPOINT_URL + '/resource'
        mock_request.assert_called_with(expected_url, 'GET',
                                        headers=expected_headers,
                                        content_type=None)

    def test_get_endpoint_url_with_invalid_auth_url(self):
        # Handle the case when auth_url is not provided
        self.client.auth_url = None
        self.assertRaises(exceptions.NoAuthURLProvided,
                          self.client._get_endpoint_url)

    @mock.patch('tackerclient.client.HTTPClient.request')
    def test_get_endpoint_url(self, mock_request):

        self.client.auth_token = TOKEN

        mock_request.return_value = (resp_200, json.dumps(ENDPOINTS_RESULT))
        self.client.do_request('/resource', 'GET')
        mock_request.assert_called_with(
            ENDPOINT_URL + '/resource', 'GET',
            headers=expected_headers, content_type=None)

        mock_request.return_value = (resp_200, '')
        self.client.do_request('/resource', 'GET',
                               headers=headers)
        mock_request.assert_called_with(
            ENDPOINT_URL + '/resource', 'GET',
            headers=headers, content_type=None)

    @mock.patch('tackerclient.client.HTTPClient.request')
    def test_use_given_endpoint_url(self, mock_request):
        self.client = client.HTTPClient(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION,
            endpoint_url=ENDPOINT_OVERRIDE)
        self.assertEqual(self.client.endpoint_url, ENDPOINT_OVERRIDE)

        self.client.auth_token = TOKEN
        mock_request.return_value = (resp_200, '')

        self.client.do_request('/resource', 'GET',
                               headers=headers)
        mock_request.assert_called_with(
            ENDPOINT_OVERRIDE + '/resource', 'GET',
            headers=headers, content_type=None)
        self.assertEqual(self.client.endpoint_url, ENDPOINT_OVERRIDE)

    @mock.patch('tackerclient.client.HTTPClient.request')
    def test_get_endpoint_url_other(self, mock_request):
        self.client = client.HTTPClient(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION, endpoint_type='otherURL')

        self.client.auth_token = TOKEN
        mock_request.return_value = (resp_200, json.dumps(ENDPOINTS_RESULT))
        self.assertRaises(exceptions.EndpointTypeNotFound,
                          self.client.do_request,
                          '/resource',
                          'GET')
        expected_url = AUTH_URL + '/tokens/%s/endpoints' % TOKEN
        headers = {'User-Agent': 'python-tackerclient'}
        mock_request.assert_called_with(expected_url, 'GET',
                                        headers=headers)

    @mock.patch('tackerclient.client.HTTPClient.request')
    def test_get_endpoint_url_failed(self, mock_request):

        self.client.auth_token = TOKEN
        self.client.auth_url = AUTH_URL + '/tokens/%s/endpoints' % TOKEN

        mock_request.return_value = (resp_401, '')
        self.assertRaises(exceptions.Unauthorized,
                          self.client.do_request,
                          '/resource',
                          'GET')

    def test_endpoint_type(self):
        resources = copy.deepcopy(KS_TOKEN_RESULT)
        endpoints = resources['access']['serviceCatalog'][0]['endpoints'][0]
        endpoints['internalURL'] = 'internal'
        endpoints['adminURL'] = 'admin'
        endpoints['publicURL'] = 'public'

        # Test default behavior is to choose public.
        self.client = client.HTTPClient(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION)

        self.client._extract_service_catalog(resources)
        self.assertEqual(self.client.endpoint_url, 'public')

        # Test admin url
        self.client = client.HTTPClient(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION, endpoint_type='adminURL')

        self.client._extract_service_catalog(resources)
        self.assertEqual(self.client.endpoint_url, 'admin')

        # Test public url
        self.client = client.HTTPClient(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION, endpoint_type='publicURL')

        self.client._extract_service_catalog(resources)
        self.assertEqual(self.client.endpoint_url, 'public')

        # Test internal url
        self.client = client.HTTPClient(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION, endpoint_type='internalURL')

        self.client._extract_service_catalog(resources)
        self.assertEqual(self.client.endpoint_url, 'internal')

        # Test url that isn't found in the service catalog
        self.client = client.HTTPClient(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION, endpoint_type='privateURL')

        self.assertRaises(k_exceptions.EndpointNotFound,
                          self.client._extract_service_catalog,
                          resources)

    @mock.patch('tackerclient.client.HTTPClient.request')
    @mock.patch('tackerclient.common.utils.http_log_req')
    def test_strip_credentials_from_log(self, mock_http_log_req,
                                        mock_request,):

        body = ('{"auth": {"tenantId": "testtenant_id",'
                '"passwordCredentials": {"password": "password",'
                '"userId": "testuser_id"}}}')
        expected_body = ('{"auth": {"tenantId": "testtenant_id",'
                         '"REDACTEDCredentials": {"REDACTED": "REDACTED",'
                         '"userId": "testuser_id"}}}')
        _headers = {'headers': expected_headers, 'body': expected_body,
                    'content_type': None}

        mock_request.return_value = (resp_200, json.dumps(KS_TOKEN_RESULT))
        self.client.do_request('/resource', 'GET', body=body)

        args, kwargs = mock_http_log_req.call_args
        # Check that credentials are stripped while logging.
        self.assertEqual(_headers, args[2])


class CLITestAuthKeystoneWithId(CLITestAuthKeystone):

    # Auth Body expected
    auth_body = ('{"auth": {"passwordCredentials": '
                 '{"password": "password", "userId": "testuser_id"}, '
                 '"tenantId": "testtenant_id"}}')

    def setUp(self):
        """Prepare the test environment."""
        super(CLITestAuthKeystoneWithId, self).setUp()
        self.client = client.HTTPClient(user_id=USER_ID,
                                        tenant_id=TENANT_ID,
                                        password=PASSWORD,
                                        auth_url=AUTH_URL,
                                        region_name=REGION)


class CLITestAuthKeystoneWithIdandName(CLITestAuthKeystone):

    # Auth Body expected
    auth_body = ('{"auth": {"passwordCredentials": '
                 '{"password": "password", "userId": "testuser_id"}, '
                 '"tenantId": "testtenant_id"}}')

    def setUp(self):
        """Prepare the test environment."""
        super(CLITestAuthKeystoneWithIdandName, self).setUp()
        self.client = client.HTTPClient(username=USERNAME,
                                        user_id=USER_ID,
                                        tenant_id=TENANT_ID,
                                        tenant_name=TENANT_NAME,
                                        password=PASSWORD,
                                        auth_url=AUTH_URL,
                                        region_name=REGION)
