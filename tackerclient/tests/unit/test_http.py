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

import testtools
from unittest import mock

from tackerclient.client import HTTPClient
from tackerclient.common import exceptions
from tackerclient.tests.unit.test_cli10 import MyResp


AUTH_TOKEN = 'test_token'
END_URL = 'test_url'
METHOD = 'GET'
URL = 'http://test.test:1234/v1.0/test'
headers = {'User-Agent': 'python-tackerclient'}


class TestHTTPClient(testtools.TestCase):

    def setUp(self):

        super(TestHTTPClient, self).setUp()
        self.addCleanup(mock.patch.stopall)
        self.http = HTTPClient(token=AUTH_TOKEN, endpoint_url=END_URL)

    @mock.patch('tackerclient.client.HTTPClient.request')
    def test_request_error(self, mock_request):

        mock_request.side_effect = Exception('error msg')
        self.assertRaises(
            exceptions.ConnectionFailed,
            self.http._cs_request,
            URL, METHOD
        )

    @mock.patch('tackerclient.client.HTTPClient.request')
    def test_request_success(self, mock_request):

        rv_should_be = MyResp(200), 'test content'
        mock_request.return_value = rv_should_be
        self.assertEqual(rv_should_be, self.http._cs_request(URL, METHOD))

    @mock.patch('tackerclient.client.HTTPClient.request')
    def test_request_unauthorized(self, mock_request):

        mock_request.return_value = MyResp(401), 'unauthorized message'

        e = self.assertRaises(exceptions.Unauthorized,
                              self.http._cs_request, URL, METHOD)
        self.assertEqual('unauthorized message', str(e))
        mock_request.assert_called_with(URL, METHOD, headers=headers)

    @mock.patch('tackerclient.client.HTTPClient.request')
    def test_request_forbidden_is_returned_to_caller(self, mock_request):

        rv_should_be = MyResp(403), 'forbidden message'
        mock_request.return_value = rv_should_be
        self.assertEqual(rv_should_be, self.http._cs_request(URL, METHOD))
