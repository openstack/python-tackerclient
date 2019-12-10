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
from io import StringIO
import mock
import os
import sys

from oslo_utils.fixture import uuidsentinel

from tackerclient.common import exceptions
from tackerclient.osc.v1.vnflcm import vnflcm
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v1 import vnflcm_fakes
from tackerclient.v1_0 import client as proxy_client


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


def _get_columns_vnflcm(action='create'):
    columns = ['ID', 'Instantiation State', 'VNF Instance Description',
               'VNF Instance Name', 'VNF Product Name', 'VNF Provider',
               'VNF Software Version', 'VNFD ID', 'VNFD Version', 'Links']
    if action == 'show':
        columns.extend(['Instantiated Vnf Info', 'VIM Connection Info'])
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

    @ddt.data({"optional_arguments": True, "instantiate": True},
              {"optional_arguments": False, "instantiate": False})
    @ddt.unpack
    def test_take_action(self, optional_arguments, instantiate):
        arglist = [uuidsentinel.vnf_package_vnfd_id]
        verifylist = [('vnfd_id', uuidsentinel.vnf_package_vnfd_id)]

        if optional_arguments:
            arglist.extend(['--name', 'test',
                            '--description', 'test'])
            verifylist.extend([('name', 'test'),
                               ('description', 'test')])

        # command param
        if instantiate:
            param_file = ("./tackerclient/osc/v1/vnflcm/samples/"
                          "instantiate_vnf_instance_param_sample.json")

            arglist.extend(['--I', param_file])
            verifylist.append(('I', param_file))

        parsed_args = self.check_parser(self.create_vnf_lcm, arglist,
                                        verifylist)

        json = vnflcm_fakes.vnf_instance_response()
        self.requests_mock.register_uri(
            'POST', os.path.join(self.url, 'vnflcm/v1/vnf_instances'),
            json=json, headers=self.header)

        if instantiate:
            self.requests_mock.register_uri(
                'POST', os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                                     json['id'], 'instantiate'),
                json={}, headers=self.header)

        sys.stdout = buffer = StringIO()
        columns, data = (self.create_vnf_lcm.take_action(parsed_args))

        expected_message = (
            'VNF Instance ' + json['id'] + ' is created and instantiation '
                                           'request has been accepted.')
        if instantiate:
            self.assertEqual(expected_message, buffer.getvalue().strip())

        self.assertItemsEqual(_get_columns_vnflcm(),
                              columns)
        self.assertItemsEqual(vnflcm_fakes.get_vnflcm_data(json),
                              data)


class TestShowVnfLcm(TestVnfLcm):

    def setUp(self):
        super(TestShowVnfLcm, self).setUp()
        self.show_vnf_lcm = vnflcm.ShowVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm show')

    def test_take_action(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response(
            instantiation_state='INSTANTIATED')

        arglist = [vnf_instance['id']]
        verifylist = [('vnf_instance', vnf_instance['id'])]

        # command param
        parsed_args = self.check_parser(self.show_vnf_lcm, arglist,
                                        verifylist)

        self.requests_mock.register_uri(
            'GET', os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                                vnf_instance['id']),
            json=vnf_instance, headers=self.header)

        columns, data = (self.show_vnf_lcm.take_action(parsed_args))
        self.assertItemsEqual(_get_columns_vnflcm(action='show'),
                              columns)


class TestInstantiateVnfLcm(TestVnfLcm):

    def setUp(self):
        super(TestInstantiateVnfLcm, self).setUp()
        self.instantiate_vnf_lcm = vnflcm.InstantiateVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm instantiate')

    def test_take_action(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = ("./tackerclient/osc/v1/vnflcm/samples/"
                             "instantiate_vnf_instance_param_sample.json")

        arglist = [vnf_instance['id'], sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('instantiation_request_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.instantiate_vnf_lcm, arglist,
                                        verifylist)

        url = os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                           vnf_instance['id'], 'instantiate')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, json={})

        sys.stdout = buffer = StringIO()
        with mock.patch.object(proxy_client.ClientBase,
                               '_handle_fault_response') as m:
            self.instantiate_vnf_lcm.take_action(parsed_args)
            # check no fault response is received
            self.assertNotCalled(m)
            self.assertEqual(
                'Instantiate request for VNF Instance ' + vnf_instance['id'] +
                ' has been accepted.', buffer.getvalue().strip())

    def test_take_action_vnf_instance_not_found(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = ("./tackerclient/osc/v1/vnflcm/samples/"
                             "instantiate_vnf_instance_param_sample.json")
        arglist = [vnf_instance['id'], sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('instantiation_request_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.instantiate_vnf_lcm, arglist,
                                        verifylist)

        url = os.path.join(self.url, 'vnflcm/v1/vnf_instances',
                           vnf_instance['id'], 'instantiate')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.instantiate_vnf_lcm.take_action,
                          parsed_args)

    def test_take_action_param_file_not_exists(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = "./not_exists.json"
        arglist = [vnf_instance['id'], sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('instantiation_request_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.instantiate_vnf_lcm, arglist,
                                        verifylist)

        ex = self.assertRaises(exceptions.InvalidInput,
                               self.instantiate_vnf_lcm.take_action,
                               parsed_args)

        expected_msg = ("File %s does not exist or user does not have read "
                        "privileges to it")
        self.assertEqual(expected_msg % sample_param_file, ex.message)

    @mock.patch("os.open")
    @mock.patch("os.access")
    def test_take_action_invalid_format_param_file(self, mock_open,
                                                   mock_access):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = "./invalid_param_file.json"
        arglist = [vnf_instance['id'], sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('instantiation_request_file', sample_param_file)]

        mock_open.return_value = "invalid_json_data"
        # command param
        parsed_args = self.check_parser(self.instantiate_vnf_lcm, arglist,
                                        verifylist)

        ex = self.assertRaises(exceptions.InvalidInput,
                               self.instantiate_vnf_lcm.take_action,
                               parsed_args)

        expected_msg = "Failed to load parameter file."
        self.assertIn(expected_msg, ex.message)
