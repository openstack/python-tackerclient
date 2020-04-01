# Copyright (C) 2020 NTT DATA
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
import os

from oslo_utils.fixture import uuidsentinel

from tackerclient.osc.v1.vnflcm import vnflcm
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v1 import vnflcm_fakes


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


def _get_columns_vnflcm():
    columns = ['ID', 'Instantiation State', 'VNF Instance Description',
               'VNF Instance Name', 'VNF Product Name', 'VNF Provider',
               'VNF Software Version', 'VNFD ID', 'VNFD Version', 'Links']
    return columns


@ddt.ddt
class TestCreateVnfLcm(TestVnfLcm):

    def setUp(self):
        super(TestCreateVnfLcm, self).setUp()
        self.create_vnf_lcm = vnflcm.CreateVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm create')

    def test_create_no_args(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.create_vnf_lcm, [], [])

    @ddt.data(True, False)
    def test_take_action(self, optional_arguments):
        arglist = [uuidsentinel.vnf_package_vnfd_id]
        verifylist = [('vnfd_id', uuidsentinel.vnf_package_vnfd_id)]

        if optional_arguments:
            arglist.extend(['--name', 'test',
                            '--description', 'test'])
            verifylist.extend([('name', 'test'),
                               ('description', 'test')])

        # command param
        parsed_args = self.check_parser(self.create_vnf_lcm, arglist,
                                        verifylist)

        json = vnflcm_fakes.vnf_instance_response()
        self.requests_mock.register_uri(
            'POST', os.path.join(self.url, 'vnflcm/v1/vnf_instances'),
            json=json, headers=self.header)

        columns, data = (self.create_vnf_lcm.take_action(parsed_args))
        self.assertItemsEqual(_get_columns_vnflcm(),
                              columns)
        self.assertItemsEqual(vnflcm_fakes.get_vnflcm_data(json),
                              data)
