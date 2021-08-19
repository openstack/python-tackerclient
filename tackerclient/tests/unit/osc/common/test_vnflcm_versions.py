# Copyright (C) 2021 Nippon Telegraph and Telephone Corporation
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

import os

import ddt
from unittest import mock

from tackerclient.common import exceptions
from tackerclient.osc.common.vnflcm import vnflcm_versions
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client


class TestVnfLcm(base.FixturedTestCase):
    client_fixture_class = client.ClientFixture

    def setUp(self):
        super(TestVnfLcm, self).setUp()
        self.url = client.TACKER_URL
        self.header = {'content-type': 'application/json'}
        self.app = mock.Mock()
        self.app_args = mock.Mock()
        self.client_manager = self.cs
        self.app.client_manager.tackerclient = self.client_manager


@ddt.ddt
class TestVnfLcmVersions(TestVnfLcm):

    def setUp(self):
        super(TestVnfLcmVersions, self).setUp()
        self.vnflcm_versions = vnflcm_versions.VnfLcmVersions(
            self.app, self.app_args, cmd_name='vnflcm versions')

    def _versions_response(self, major_version=None):
        if major_version is None:
            return {"uriPrefix": "/vnflcm",
                    "apiVersions": [{"version": "1.3.0",
                                     "isDeprecated": False},
                                    {"version": "2.0.0",
                                     "isDeprecated": False}]}
        elif major_version == "1":
            return {"uriPrefix": "/vnflcm/v1",
                    "apiVersions": [{"version": "1.3.0",
                                     "isDeprecated": False}]}
        elif major_version == "2":
            return {"uriPrefix": "/vnflcm/v2",
                    "apiVersions": [{"version": "2.0.0",
                                     "isDeprecated": False}]}

    def test_invalid_major_version(self):
        parser = self.vnflcm_versions.get_parser('vnflcm versions')
        parsed_args = parser.parse_args(["--major-version", "3"])
        self.assertRaises(exceptions.InvalidInput,
                          self.vnflcm_versions.take_action,
                          parsed_args)

    def test_take_action_no_arg(self):
        parser = self.vnflcm_versions.get_parser('vnflcm versions')
        parsed_args = parser.parse_args([])

        response = self._versions_response()
        self.requests_mock.register_uri(
            'GET', os.path.join(self.url, 'vnflcm/api_versions'),
            json=response, headers=self.header)

        colmns, data = self.vnflcm_versions.take_action(parsed_args)

        self.assertEqual(colmns, tuple(response.keys()))
        self.assertEqual(data, tuple(response.values()))

    @ddt.data('1', '2')
    def test_take_action_with_major_version(self, major_version):
        parser = self.vnflcm_versions.get_parser('vnflcm versions')
        parsed_args = parser.parse_args(["--major-version",
                                         major_version])

        response = self._versions_response(major_version)
        self.requests_mock.register_uri(
            'GET',
            os.path.join(self.url,
                         'vnflcm/v{}/api_versions'.format(major_version)),
            json=response, headers=self.header)

        colmns, data = self.vnflcm_versions.take_action(parsed_args)

        self.assertEqual(colmns, tuple(response.keys()))
        self.assertEqual(data, tuple(response.values()))
