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

from oslo_utils.fixture import uuidsentinel
from unittest import mock

from tackerclient.common import exceptions
from tackerclient.osc.v1.vnflcm import vnflcm_op_occs
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


class TestRollbackVnfLcmOp(TestVnfLcm):

    def setUp(self):
        super(TestRollbackVnfLcmOp, self).setUp()
        self.rollback_vnf_lcm = vnflcm_op_occs.RollbackVnfLcmOp(
            self.app, self.app_args, cmd_name='vnflcm op rollback')

    def test_take_action(self):
        """take_action normal system test"""

        arglist = [uuidsentinel.vnf_lcm_op_occ_id]
        verifylist = [('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        parsed_args = self.check_parser(
            self.rollback_vnf_lcm, arglist, verifylist)
        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id,
            'rollback')

        self.requests_mock.register_uri(
            'POST', url, headers=self.header, json={})

        sys.stdout = buffer = StringIO()
        self.rollback_vnf_lcm.take_action(parsed_args)

        actual_message = buffer.getvalue().strip()

        expected_message = (
            'Rollback request for LCM operation ' +
            uuidsentinel.vnf_lcm_op_occ_id +
            ' has been accepted')

        self.assertEqual(expected_message, actual_message)

    def test_take_action_vnf_lcm_op_occ_id_not_found(self):
        """take_action abnomaly system test"""

        arglist = [uuidsentinel.vnf_lcm_op_occ_id]
        verifylist = [('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        parsed_args = self.check_parser(
            self.rollback_vnf_lcm, arglist, verifylist)

        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id,
            'rollback')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.rollback_vnf_lcm.take_action,
                          parsed_args)
