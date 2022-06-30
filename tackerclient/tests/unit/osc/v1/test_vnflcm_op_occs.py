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

import copy
from io import StringIO
import os
import sys

import ddt
from oslo_utils.fixture import uuidsentinel
from unittest import mock

from tackerclient.common import exceptions
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.osc.v1.vnflcm import vnflcm_op_occs
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v1 import vnflcm_op_occs_fakes


def _get_columns_vnflcm_op_occs(action='show', parameter=None):

    if action == 'fail':
        return ['ID', 'Operation State', 'State Entered Time',
                'Start Time', 'VNF Instance ID', 'Operation',
                'Is Automatic Invocation', 'Is Cancel Pending',
                'Error', 'Links']
    elif action == 'list':
        if parameter is not None:
            return ['ID', 'Operation']
        else:
            return ['ID', 'Operation State', 'VNF Instance ID',
                    'Operation']
    else:
        return ['ID', 'Operation State', 'State Entered Time',
                'Start Time', 'VNF Instance ID', 'Grant ID',
                'Operation', 'Is Automatic Invocation',
                'Operation Parameters', 'Is Cancel Pending',
                'Cancel Mode', 'Error', 'Resource Changes',
                'Changed Info', 'Changed External Connectivity', 'Links']


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
class TestCancelVnfLcmOp(TestVnfLcm):

    def setUp(self):
        super(TestCancelVnfLcmOp, self).setUp()
        self.cancel_vnf_lcm = vnflcm_op_occs.CancelVnfLcmOp(
            self.app, self.app_args, cmd_name='vnflcm op cancel')

    @ddt.data('GRACEFUL', 'FORCEFUL')
    def test_take_action(self, cancel_mode):
        """take_action normal system test"""

        arglist = ['--cancel-mode', cancel_mode,
                   uuidsentinel.vnf_lcm_op_occ_id]
        verifylist = [('cancel_mode', cancel_mode),
                      ('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        parsed_args = self.check_parser(
            self.cancel_vnf_lcm, arglist, verifylist)
        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id,
            'cancel')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, json={})

        sys.stdout = buffer = StringIO()
        self.cancel_vnf_lcm.take_action(parsed_args)

        actual_message = buffer.getvalue().strip()

        expected_message = (
            'Cancel request for LCM operation ' +
            uuidsentinel.vnf_lcm_op_occ_id +
            ' has been accepted')

        self.assertEqual(expected_message, actual_message)

    def test_terminate_no_options(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.cancel_vnf_lcm, [], [])

    def test_take_action_vnf_lcm_op_occ_id_not_found(self):
        """take_action abnomaly system test"""

        arglist = [uuidsentinel.vnf_lcm_op_occ_id]
        verifylist = [('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        parsed_args = self.check_parser(
            self.cancel_vnf_lcm, arglist, verifylist)
        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id,
            'cancel')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.cancel_vnf_lcm.take_action,
                          parsed_args)


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


class TestFailVnfLcmOp(TestVnfLcm):

    def setUp(self):
        super(TestFailVnfLcmOp, self).setUp()
        self.fail_vnf_lcm = vnflcm_op_occs.FailVnfLcmOp(
            self.app, self.app_args, cmd_name='vnflcm op fail')

    def test_take_action(self):
        """Test of take_action()"""

        vnflcm_op_occ = vnflcm_op_occs_fakes.vnflcm_op_occ_response(
            action='fail')

        arg_list = [vnflcm_op_occ['id']]
        verify_list = [('vnf_lcm_op_occ_id', vnflcm_op_occ['id'])]

        # command param
        parsed_args = self.check_parser(
            self.fail_vnf_lcm, arg_list, verify_list)
        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            vnflcm_op_occ['id'],
            'fail')

        self.requests_mock.register_uri(
            'POST', url, headers=self.header, json=vnflcm_op_occ)

        columns, data = (self.fail_vnf_lcm.take_action(parsed_args))
        expected_columns = _get_columns_vnflcm_op_occs(action='fail')

        self.assertCountEqual(expected_columns, columns)

    def test_take_action_vnf_lcm_op_occ_id_not_found(self):
        """Test if vnf-lcm-op-occ-id does not find"""

        arg_list = [uuidsentinel.vnf_lcm_op_occ_id]
        verify_list = [('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        # command param
        parsed_args = self.check_parser(
            self.fail_vnf_lcm, arg_list, verify_list)

        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id,
            'fail')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.fail_vnf_lcm.take_action,
                          parsed_args)

    def test_take_action_vnf_lcm_op_occ_state_is_conflict(self):
        """Test if vnf-lcm-op-occ state is conflict"""

        arg_list = [uuidsentinel.vnf_lcm_op_occ_id]
        verify_list = [('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        # command param
        parsed_args = self.check_parser(
            self.fail_vnf_lcm, arg_list, verify_list)

        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id,
            'fail')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=409, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.fail_vnf_lcm.take_action,
                          parsed_args)

    def test_take_action_vnf_lcm_op_occ_internal_server_error(self):
        """Test if request is internal server error"""

        arg_list = [uuidsentinel.vnf_lcm_op_occ_id]
        verify_list = [('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        # command param
        parsed_args = self.check_parser(
            self.fail_vnf_lcm, arg_list, verify_list)

        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id,
            'fail')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=500, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.fail_vnf_lcm.take_action,
                          parsed_args)

    def test_take_action_vnf_lcm_op_occ_missing_vnf_lcm_op_occ_id_argument(
        self):
        """Test if vnflcm_op_occ_id is not provided"""

        arg_list = []
        verify_list = [('vnf_lcm_op_occ_id', arg_list)]
        self.assertRaises(base.ParserException, self.check_parser,
                          self.fail_vnf_lcm, arg_list, verify_list)


class TestRetryVnfLcmOp(TestVnfLcm):

    def setUp(self):
        super(TestRetryVnfLcmOp, self).setUp()
        self.retry_vnf_lcm = vnflcm_op_occs.RetryVnfLcmOp(
            self.app, self.app_args, cmd_name='vnflcm op retry')

    def test_take_action(self):
        """Test of take_action()"""
        arg_list = [uuidsentinel.vnf_lcm_op_occ_id]
        verify_list = [('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        # command param
        parsed_args = self.check_parser(
            self.retry_vnf_lcm, arg_list, verify_list)
        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id,
            'retry')

        self.requests_mock.register_uri(
            'POST', url, headers=self.header, json={})

        sys.stdout = buffer = StringIO()
        self.retry_vnf_lcm.take_action(parsed_args)

        actual_message = buffer.getvalue().strip()

        expected_message = (
            'Retry request for LCM operation ' +
            uuidsentinel.vnf_lcm_op_occ_id +
            ' has been accepted')

        self.assertEqual(expected_message, actual_message)

    def test_take_action_vnf_lcm_op_occ_id_not_found(self):
        """Test if vnf-lcm-op-occ-id is not found."""
        arglist = [uuidsentinel.vnf_lcm_op_occ_id]
        verifylist = [('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        # command param
        parsed_args = self.check_parser(
            self.retry_vnf_lcm, arglist, verifylist)

        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id,
            'retry')

        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.retry_vnf_lcm.take_action,
                          parsed_args)

    def test_take_action_vnf_lcm_op_occ_state_is_conflict(self):
        """Test if vnf-lcm-op-occ state is conflict"""

        arg_list = [uuidsentinel.vnf_lcm_op_occ_id]
        verify_list = [('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        # command param
        parsed_args = self.check_parser(
            self.retry_vnf_lcm, arg_list, verify_list)

        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id,
            'retry')

        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=409, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.retry_vnf_lcm.take_action,
                          parsed_args)

    def test_take_action_vnf_lcm_op_occ_internal_server_error(self):
        """Test if request is internal server error"""

        arg_list = [uuidsentinel.vnf_lcm_op_occ_id]
        verify_list = [('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        # command param
        parsed_args = self.check_parser(
            self.retry_vnf_lcm, arg_list, verify_list)

        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id,
            'retry')

        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=500, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.retry_vnf_lcm.take_action,
                          parsed_args)

    def test_take_action_vnf_lcm_op_occ_missing_vnf_lcm_op_occ_id_argument(
        self):
        """Test if vnflcm_op_occ_id is not provided"""

        arg_list = []
        verify_list = [('vnf_lcm_op_occ_id', arg_list)]
        self.assertRaises(base.ParserException, self.check_parser,
                          self.retry_vnf_lcm, arg_list, verify_list)


class TestListVnfLcmOp(TestVnfLcm):

    def setUp(self):
        super(TestListVnfLcmOp, self).setUp()
        self.list_vnflcm_op_occ = vnflcm_op_occs.ListVnfLcmOp(
            self.app, self.app_args, cmd_name='vnflcm op list')

    def test_take_action(self):
        vnflcm_op_occs_obj = vnflcm_op_occs_fakes.create_vnflcm_op_occs(
            count=3)
        parsed_args = self.check_parser(self.list_vnflcm_op_occ, [], [])
        self.requests_mock.register_uri(
            'GET', os.path.join(self.url,
                                'vnflcm/v1/vnf_lcm_op_occs'),
            json=vnflcm_op_occs_obj, headers=self.header)

        actual_columns, data = self.list_vnflcm_op_occ.take_action(parsed_args)

        headers, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnflcm_op_occ.get_attributes(), long_listing=True)

        expected_data = []
        for vnflcm_op_occ_obj_idx in vnflcm_op_occs_obj:
            expected_data.append(vnflcm_op_occs_fakes.get_vnflcm_op_occ_data(
                vnflcm_op_occ_obj_idx, columns=columns))

        self.assertCountEqual(_get_columns_vnflcm_op_occs(action='list'),
                              actual_columns)
        self.assertCountEqual(expected_data, list(data))

    def test_take_action_with_filter(self):
        vnflcm_op_occs_obj = vnflcm_op_occs_fakes.create_vnflcm_op_occs(
            count=3)
        parsed_args = self.check_parser(
            self.list_vnflcm_op_occ,
            ["--filter", '(eq,operationState,STARTING)'],
            [('filter', '(eq,operationState,STARTING)')])
        self.requests_mock.register_uri(
            'GET', os.path.join(
                self.url,
                'vnflcm/v1/vnf_lcm_op_occs?'
                'filter=(eq,operationState,STARTING)'),
            json=vnflcm_op_occs_obj, headers=self.header)

        actual_columns, data = self.list_vnflcm_op_occ.take_action(parsed_args)

        headers, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnflcm_op_occ.get_attributes(), long_listing=True)

        expected_data = []
        for vnflcm_op_occ_obj_idx in vnflcm_op_occs_obj:
            expected_data.append(vnflcm_op_occs_fakes.get_vnflcm_op_occ_data(
                vnflcm_op_occ_obj_idx, columns=columns))

        self.assertCountEqual(_get_columns_vnflcm_op_occs(action='list'),
                              actual_columns)
        self.assertListItemsEqual(expected_data, list(data))

    def test_take_action_with_incorrect_filter(self):

        parsed_args = self.check_parser(
            self.list_vnflcm_op_occ,
            ["--filter", '(operationState)'],
            [('filter', '(operationState)')])

        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs?filter=(operationState)')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=400, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.list_vnflcm_op_occ.take_action,
                          parsed_args)

    def test_take_action_internal_server_error(self):

        parsed_args = self.check_parser(
            self.list_vnflcm_op_occ,
            ["--filter", '(eq,operationState,STARTING)'],
            [('filter', '(eq,operationState,STARTING)')])

        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs?'
            'filter=(eq,operationState,STARTING)')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=500, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.list_vnflcm_op_occ.take_action,
                          parsed_args)

    def test_take_action_with_exclude_fields(self):

        vnflcm_op_occs_obj = vnflcm_op_occs_fakes.create_vnflcm_op_occs(
            count=3)
        parsed_args = self.check_parser(
            self.list_vnflcm_op_occ,
            ["--exclude-fields", 'VNF Instance ID,Operation State'],
            [('exclude_fields', 'VNF Instance ID,Operation State')])
        self.requests_mock.register_uri(
            'GET', os.path.join(
                self.url,
                'vnflcm/v1/vnf_lcm_op_occs?'
                'exclude-fields=VNF Instance ID,Operation State'),
            json=vnflcm_op_occs_obj, headers=self.header)
        actual_columns, data = self.list_vnflcm_op_occ.take_action(parsed_args)
        headers, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnflcm_op_occ.get_attributes(
                exclude=['VNF Instance ID', 'Operation State']),
            long_listing=True)
        expected_data = []
        for vnflcm_op_occ_obj_idx in vnflcm_op_occs_obj:
            expected_data.append(
                vnflcm_op_occs_fakes.get_vnflcm_op_occ_data(
                    vnflcm_op_occ_obj_idx, columns=columns))

        self.assertCountEqual(_get_columns_vnflcm_op_occs(
            action='list', parameter="exclude_fields"),
            actual_columns)
        self.assertListItemsEqual(expected_data, list(data))

    def test_take_action_with_pagination(self):
        next_links_num = 3
        vnflcm_op_occs_obj = vnflcm_op_occs_fakes.create_vnflcm_op_occs(
            count=next_links_num)
        parsed_args = self.check_parser(self.list_vnflcm_op_occ, [], [])
        path = os.path.join(self.url, 'vnflcm/v1/vnf_lcm_op_occs')

        links = [0] * next_links_num
        link_headers = [0] * next_links_num

        for i in range(next_links_num):
            links[i] = (
                '{base_url}?nextpage_opaque_marker={vnflcm_op_occ_id}'.format(
                    base_url=path,
                    vnflcm_op_occ_id=vnflcm_op_occs_obj[i]['id']))
            link_headers[i] = copy.deepcopy(self.header)
            link_headers[i]['Link'] = '<{link_url}>; rel="next"'.format(
                link_url=links[i])

        self.requests_mock.register_uri(
            'GET', path, json=[vnflcm_op_occs_obj[0]], headers=link_headers[0])
        self.requests_mock.register_uri(
            'GET', links[0], json=[vnflcm_op_occs_obj[1]],
            headers=link_headers[1])
        self.requests_mock.register_uri(
            'GET', links[1], json=[vnflcm_op_occs_obj[2]],
            headers=link_headers[2])
        self.requests_mock.register_uri(
            'GET', links[2], json=[], headers=self.header)

        actual_columns, data = self.list_vnflcm_op_occ.take_action(parsed_args)

        headers, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnflcm_op_occ.get_attributes(), long_listing=True)

        expected_data = []
        for vnflcm_op_occ_obj_idx in vnflcm_op_occs_obj:
            expected_data.append(vnflcm_op_occs_fakes.get_vnflcm_op_occ_data(
                vnflcm_op_occ_obj_idx, columns=columns))

        self.assertCountEqual(_get_columns_vnflcm_op_occs(action='list'),
                              actual_columns)
        self.assertCountEqual(expected_data, list(data))


class TestShowVnfLcmOp(TestVnfLcm):

    def setUp(self):
        super(TestShowVnfLcmOp, self).setUp()
        self.show_vnf_lcm_op_occs = vnflcm_op_occs.ShowVnfLcmOp(
            self.app, self.app_args, cmd_name='vnflcm op show')

    def test_take_action(self):
        """Test of take_action()"""
        vnflcm_op_occ = vnflcm_op_occs_fakes.vnflcm_op_occ_response()

        arglist = [vnflcm_op_occ['id']]
        verifylist = [('vnf_lcm_op_occ_id', vnflcm_op_occ['id'])]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_lcm_op_occs, arglist, verifylist)
        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            vnflcm_op_occ['id'])

        self.requests_mock.register_uri(
            'GET', url, headers=self.header, json=vnflcm_op_occ)

        columns, data = (self.show_vnf_lcm_op_occs.take_action(parsed_args))

        self.assertCountEqual(_get_columns_vnflcm_op_occs(),
                              columns)

    def test_take_action_vnf_lcm_op_occ_id_not_found(self):
        """Test if vnf-lcm-op-occ-id does not find."""
        arglist = [uuidsentinel.vnf_lcm_op_occ_id]
        verifylist = [('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_lcm_op_occs, arglist, verifylist)

        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id)
        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.show_vnf_lcm_op_occs.take_action,
                          parsed_args)

    def test_take_action_internal_server_error(self):
        """Test for internal server error."""
        arglist = [uuidsentinel.vnf_lcm_op_occ_id]
        verifylist = [('vnf_lcm_op_occ_id', uuidsentinel.vnf_lcm_op_occ_id)]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_lcm_op_occs, arglist, verifylist)

        url = os.path.join(
            self.url,
            'vnflcm/v1/vnf_lcm_op_occs',
            uuidsentinel.vnf_lcm_op_occ_id)
        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=500, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.show_vnf_lcm_op_occs.take_action,
                          parsed_args)
