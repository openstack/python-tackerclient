# Copyright (C) 2019 NTT DATA
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

import ddt
import mock

from tackerclient.osc.v1.vnfpkgm import vnf_package
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v1 import vnf_package_fakes


class TestVnfPackage(base.FixturedTestCase):
    client_fixture_class = client.ClientFixture

    def setUp(self):
        super(TestVnfPackage, self).setUp()
        self.url = client.TACKER_URL
        self.app = mock.Mock()
        self.app_args = mock.Mock()
        self.client_manager = self.cs
        self.app.client_manager.tackerclient = self.client_manager


@ddt.ddt
class TestCreateVnfPackage(TestVnfPackage):

    columns = ('ID', 'Links', 'Onboarding State', 'Operational State',
               'Usage State', 'User Defined Data')

    def setUp(self):
        super(TestCreateVnfPackage, self).setUp()
        self.create_vnf_package = vnf_package.CreateVnfPackage(
            self.app, self.app_args, cmd_name='vnf package create')

    @ddt.data((["--user-data", 'Test_key=Test_value'],
               [('user_data', {'Test_key': 'Test_value'})]),
              ([], []))
    @ddt.unpack
    def test_take_action(self, arglist, verifylist):
        # command param
        parsed_args = self.check_parser(self.create_vnf_package, arglist,
                                        verifylist)
        header = {'content-type': 'application/json'}

        if arglist:
            json = vnf_package_fakes.vnf_package_obj(
                attrs={'userDefinedData': {'Test_key': 'Test_value'}})
        else:
            json = vnf_package_fakes.vnf_package_obj()
        self.requests_mock.register_uri(
            'POST', self.url + '/vnfpkgm/v1/vnf_packages',
            json=json, headers=header)

        columns, data = (self.create_vnf_package.take_action(parsed_args))
        self.assertEqual(self.columns, columns)
        self.assertItemsEqual(vnf_package_fakes.get_vnf_package_data(json),
                              data)
