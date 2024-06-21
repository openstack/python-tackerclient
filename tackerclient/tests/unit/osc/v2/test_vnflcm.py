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

from io import StringIO
import os
import sys
from unittest import mock

from tackerclient import client as root_client
from tackerclient.common import exceptions
from tackerclient.osc.v1.vnflcm import vnflcm
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v1 import test_vnflcm
from tackerclient.tests.unit.osc.v1 import vnflcm_fakes
from tackerclient.tests.unit.test_cli10 import MyResp
from tackerclient.v1_0 import client as proxy_client


class TestVnfLcmV2(base.FixturedTestCase):
    client_fixture_class = client.ClientFixture
    api_version = '2'

    def setUp(self):
        super(TestVnfLcmV2, self).setUp()

    def test_client_v2(self):
        self.assertEqual(self.cs.vnf_lcm_client.headers,
                         {'Version': '2.0.0'})
        self.assertEqual(self.cs.vnf_lcm_client.vnf_instances_path,
                         '/vnflcm/v2/vnf_instances')
        # check of other paths is omitted.


class TestUpdateVnfLcmV2(test_vnflcm.TestVnfLcm):
    api_version = '2'

    def setUp(self):
        super(TestUpdateVnfLcmV2, self).setUp()
        self.update_vnf_lcm = vnflcm.UpdateVnfLcm(
            self.app, self.app_args, cmd_name='vnflcm modify')

    def test_take_action_check_content_type(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = ('./tackerclient/osc/v1/vnflcm/samples/'
                             'update_vnf_instance_param_sample.json')

        arglist = [vnf_instance['id'], '--I', sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('I', sample_param_file)]

        # command param
        parsed_args = self.check_parser(
            self.update_vnf_lcm, arglist, verifylist)
        url = os.path.join(self.url, 'vnflcm/v2/vnf_instances',
                           vnf_instance['id'])

        self.requests_mock.register_uri(
            'PATCH', url, headers=self.header, json={})

        sys.stdout = buffer = StringIO()

        with mock.patch.object(root_client.HTTPClient,
                               'do_request') as mock_req:
            headers = {'Content-Type': 'application/json'}
            mock_req.return_value = (MyResp(202, headers=headers), None)
            self.update_vnf_lcm.take_action(parsed_args)
            # check content_type
            mock_req.assert_called_once_with(
                f'/vnflcm/v2/vnf_instances/{vnf_instance["id"]}', 'PATCH',
                body=mock.ANY, headers=mock.ANY,
                content_type='application/merge-patch+json', accept='json')

        actual_message = buffer.getvalue().strip()
        expected_message = f'Update vnf:{vnf_instance["id"]}'
        self.assertEqual(expected_message, actual_message)


class TestChangeVnfPkgVnfLcm(test_vnflcm.TestVnfLcm):
    api_version = '2'

    def setUp(self):
        super(TestChangeVnfPkgVnfLcm, self).setUp()
        self.change_vnfpkg_vnf_lcm = vnflcm.ChangeVnfPkgVnfLcm(
            self.app, self.app_args,
            cmd_name='vnflcm change-vnfpkg')

    def test_take_action(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = ("./tackerclient/osc/v2/vnflcm/samples/"
                             "change_vnfpkg_vnf_instance_param_sample.json")

        arglist = [vnf_instance['id'], sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('request_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.change_vnfpkg_vnf_lcm,
                                        arglist,
                                        verifylist)

        url = os.path.join(self.url, 'vnflcm/v2/vnf_instances',
                           vnf_instance['id'], 'change_vnfpkg')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, json={})

        sys.stdout = buffer = StringIO()
        with mock.patch.object(proxy_client.ClientBase,
                               '_handle_fault_response') as m:
            self.change_vnfpkg_vnf_lcm.take_action(parsed_args)
            # check no fault response is received
            self.assertNotCalled(m)
            self.assertEqual(
                ('Change Current VNF Package for VNF Instance {0} '
                 'has been accepted.'.format(vnf_instance['id'])),
                buffer.getvalue().strip())

    def test_take_action_vnf_instance_not_found(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = ("./tackerclient/osc/v1/vnflcm/samples/"
                             "change_vnfpkg_vnf_instance_param_sample.json")
        arglist = [vnf_instance['id'], sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('request_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.change_vnfpkg_vnf_lcm,
                                        arglist,
                                        verifylist)

        url = os.path.join(self.url, 'vnflcm/v2/vnf_instances',
                           vnf_instance['id'], 'change_vnfpkg')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.change_vnfpkg_vnf_lcm.take_action,
                          parsed_args)

    def test_take_action_param_file_not_exists(self):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = "./not_exists.json"
        arglist = [vnf_instance['id'], sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('request_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(
            self.change_vnfpkg_vnf_lcm,
            arglist,
            verifylist)

        ex = self.assertRaises(
            exceptions.InvalidInput,
            self.change_vnfpkg_vnf_lcm.take_action,
            parsed_args)

        expected_msg = ("Invalid input: "
                        "User does not have read privileges to it")
        self.assertEqual(expected_msg, str(ex))

    @mock.patch("os.open")
    @mock.patch("os.access")
    def test_take_action_invalid_format_param_file(self, mock_access,
                                                   mock_open):
        vnf_instance = vnflcm_fakes.vnf_instance_response()
        sample_param_file = "./invalid_param_file.json"
        arglist = [vnf_instance['id'], sample_param_file]
        verifylist = [('vnf_instance', vnf_instance['id']),
                      ('request_file', sample_param_file)]

        mock_open.return_value = "invalid_json_data"
        mock_access.return_value = True
        # command param
        parsed_args = self.check_parser(self.change_vnfpkg_vnf_lcm,
                                        arglist,
                                        verifylist)

        ex = self.assertRaises(
            exceptions.InvalidInput,
            self.change_vnfpkg_vnf_lcm.take_action,
            parsed_args)

        expected_msg = "Failed to load parameter file."
        self.assertIn(expected_msg, str(ex))
