# Copyright (C) 2022 Fujitsu
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
import os

from oslo_utils.fixture import uuidsentinel
from unittest import mock

from tackerclient import client as root_client
from tackerclient.common import exceptions
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.osc.v2.vnffm import vnffm_alarm
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v2 import vnffm_alarm_fakes
from tackerclient.tests.unit.test_cli10 import MyResp
from tackerclient.v1_0 import client as proxy_client


class TestVnfFmAlarm(base.FixturedTestCase):
    client_fixture_class = client.ClientFixture

    def setUp(self):
        super(TestVnfFmAlarm, self).setUp()
        self.url = client.TACKER_URL
        self.header = {'content-type': 'application/json'}
        self.app = mock.Mock()
        self.app_args = mock.Mock()
        self.client_manager = self.cs
        self.app.client_manager.tackerclient = self.client_manager


def _get_columns_vnffm_alarm(action=None):
    if action == 'update':
        columns = ['Ack State']
    else:
        columns = ['ID', 'Managed Object Id', 'Ack State',
                   'Perceived Severity', 'Event Type', 'Probable Cause']

    if action == 'show':
        columns.extend([
            'Vnfc Instance Ids', 'Root Cause Faulty Resource',
            'Alarm Raised Time', 'Alarm Changed Time',
            'Alarm Cleared Time', 'Alarm Acknowledged Time',
            'Event Time', 'Fault Type', 'Is Root Cause',
            'Correlated Alarm Ids', 'Fault Details', 'Links'
        ])

    return columns


class TestListVnfFmAlarm(TestVnfFmAlarm):

    def setUp(self):
        super(TestListVnfFmAlarm, self).setUp()
        self.list_vnf_fm_alarms = vnffm_alarm.ListVnfFmAlarm(
            self.app, self.app_args, cmd_name='vnffm alarm list')

    def test_take_action(self):
        vnffm_alarms_obj = vnffm_alarm_fakes.create_vnf_fm_alarms(
            count=3)
        parsed_args = self.check_parser(self.list_vnf_fm_alarms, [], [])
        self.requests_mock.register_uri(
            'GET', os.path.join(self.url, 'vnffm/v1/alarms'),
            json=vnffm_alarms_obj, headers=self.header)

        actual_columns, data = self.list_vnf_fm_alarms.take_action(parsed_args)

        _, columns = tacker_osc_utils.get_column_definitions(
            vnffm_alarm._ATTR_MAP, long_listing=True)

        expected_data = []
        for vnffm_alarm_obj_idx in vnffm_alarms_obj:
            expected_data.append(vnffm_alarm_fakes.get_vnffm_alarm_data(
                vnffm_alarm_obj_idx, columns=columns))

        self.assertCountEqual(_get_columns_vnffm_alarm(action='list'),
                              actual_columns)
        self.assertCountEqual(expected_data, list(data))

    def test_take_action_with_filter(self):
        vnffm_alarms_obj = vnffm_alarm_fakes.create_vnf_fm_alarms(
            count=3)
        parsed_args = self.check_parser(
            self.list_vnf_fm_alarms,
            ["--filter", '(eq,perceivedSeverity,WARNING)'],
            [('filter', '(eq,perceivedSeverity,WARNING)')])
        self.requests_mock.register_uri(
            'GET', os.path.join(
                self.url,
                'vnffm/v1/alarms?filter=(eq,perceivedSeverity,WARNING)'),
            json=vnffm_alarms_obj, headers=self.header)

        actual_columns, data = self.list_vnf_fm_alarms.take_action(parsed_args)

        _, columns = tacker_osc_utils.get_column_definitions(
            vnffm_alarm._ATTR_MAP, long_listing=True)

        expected_data = []
        for vnffm_alarm_obj_idx in vnffm_alarms_obj:
            expected_data.append(vnffm_alarm_fakes.get_vnffm_alarm_data(
                vnffm_alarm_obj_idx, columns=columns))

        self.assertCountEqual(_get_columns_vnffm_alarm(action='list'),
                              actual_columns)
        self.assertListItemsEqual(expected_data, list(data))

    def test_take_action_with_incorrect_filter(self):

        parsed_args = self.check_parser(
            self.list_vnf_fm_alarms,
            ["--filter", '(perceivedSeverity)'],
            [('filter', '(perceivedSeverity)')])

        url = os.path.join(
            self.url, 'vnffm/v1/alarms?filter=(perceivedSeverity)')

        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=400, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.list_vnf_fm_alarms.take_action,
                          parsed_args)

    def test_take_action_internal_server_error(self):

        parsed_args = self.check_parser(
            self.list_vnf_fm_alarms,
            ["--filter", '(eq,perceivedSeverity,WARNING)'],
            [('filter', '(eq,perceivedSeverity,WARNING)')])

        url = os.path.join(
            self.url, 'vnffm/v1/alarms?filter=(eq,perceivedSeverity,WARNING)')

        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=500, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.list_vnf_fm_alarms.take_action,
                          parsed_args)


class TestShowVnfFmAlarm(TestVnfFmAlarm):

    def setUp(self):
        super(TestShowVnfFmAlarm, self).setUp()
        self.show_vnf_fm_alarm = vnffm_alarm.ShowVnfFmAlarm(
            self.app, self.app_args, cmd_name='vnffm alarm show')

    def test_take_action(self):
        """Test of take_action()"""
        vnffm_alarm_obj = vnffm_alarm_fakes.vnf_fm_alarm_response()

        arglist = [vnffm_alarm_obj['id']]
        verifylist = [('vnf_fm_alarm_id', vnffm_alarm_obj['id'])]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_fm_alarm, arglist, verifylist)

        url = os.path.join(
            self.url, 'vnffm/v1/alarms', vnffm_alarm_obj['id'])

        self.requests_mock.register_uri(
            'GET', url, headers=self.header, json=vnffm_alarm_obj)

        columns, _ = (self.show_vnf_fm_alarm.take_action(parsed_args))

        self.assertCountEqual(_get_columns_vnffm_alarm(action='show'),
                              columns)

    def test_take_action_vnf_lcm_op_occ_id_not_found(self):
        """Test if vnf-lcm-op-occ-id does not find."""
        arglist = [uuidsentinel.vnf_fm_alarm_id]
        verifylist = [('vnf_fm_alarm_id', uuidsentinel.vnf_fm_alarm_id)]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_fm_alarm, arglist, verifylist)

        url = os.path.join(
            self.url, 'vnffm/v1/alarms', uuidsentinel.vnf_fm_alarm_id)

        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.show_vnf_fm_alarm.take_action,
                          parsed_args)

    def test_take_action_internal_server_error(self):
        """Test for internal server error."""
        arglist = [uuidsentinel.vnf_fm_alarm_id]
        verifylist = [('vnf_fm_alarm_id', uuidsentinel.vnf_fm_alarm_id)]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_fm_alarm, arglist, verifylist)

        url = os.path.join(
            self.url, 'vnffm/v1/alarms', uuidsentinel.vnf_fm_alarm_id)

        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=500, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.show_vnf_fm_alarm.take_action,
                          parsed_args)


@ddt.ddt
class TestUpdateVnfFmAlarm(TestVnfFmAlarm):

    def setUp(self):
        super(TestUpdateVnfFmAlarm, self).setUp()
        self.update_vnf_fm_alarm = vnffm_alarm.UpdateVnfFmAlarm(
            self.app, self.app_args, cmd_name='vnffm alarm update')

    @ddt.data('ACKNOWLEDGED', 'UNACKNOWLEDGED')
    def test_take_action(self, ack_state):
        """Test of take_action()"""

        vnffm_alarm_obj = vnffm_alarm_fakes.vnf_fm_alarm_response(
            None, 'update')

        arg_list = ['--ack-state', ack_state, uuidsentinel.vnf_fm_alarm_id]
        verify_list = [('ack_state', ack_state),
                       ('vnf_fm_alarm_id', uuidsentinel.vnf_fm_alarm_id)]

        # command param
        parsed_args = self.check_parser(
            self.update_vnf_fm_alarm, arg_list, verify_list)

        url = os.path.join(
            self.url, 'vnffm/v1/alarms', uuidsentinel.vnf_fm_alarm_id)

        self.requests_mock.register_uri(
            'PATCH', url, headers=self.header, json=vnffm_alarm_obj)

        actual_columns, data = (
            self.update_vnf_fm_alarm.take_action(parsed_args))

        expected_columns = _get_columns_vnffm_alarm(action='update')

        self.assertCountEqual(expected_columns, actual_columns)

        _, columns = vnffm_alarm._get_columns(
            vnffm_alarm_obj, action='update')

        expected_data = vnffm_alarm_fakes.get_vnffm_alarm_data(
            vnffm_alarm_obj, columns=columns)

        self.assertEqual(expected_data, data)

    @ddt.data('ACKNOWLEDGED')
    @mock.patch.object(proxy_client.ClientBase, 'deserialize')
    def test_take_action_check_content_type(self, ack_state, mock_des):
        """Check content type by test of take_action()"""

        vnffm_alarm_obj = vnffm_alarm_fakes.vnf_fm_alarm_response(
            None, 'update')

        arg_list = ['--ack-state', ack_state, uuidsentinel.vnf_fm_alarm_id]
        verify_list = [('ack_state', ack_state),
                       ('vnf_fm_alarm_id', uuidsentinel.vnf_fm_alarm_id)]
        mock_des.return_value = {}

        # command param
        parsed_args = self.check_parser(
            self.update_vnf_fm_alarm, arg_list, verify_list)

        url = os.path.join(
            self.url, 'vnffm/v1/alarms', uuidsentinel.vnf_fm_alarm_id)

        self.requests_mock.register_uri(
            'PATCH', url, headers=self.header, json=vnffm_alarm_obj)

        with mock.patch.object(root_client.HTTPClient,
                               'do_request') as mock_req:
            headers = {'Content-Type': 'application/json'}
            mock_req.return_value = (MyResp(200, headers=headers), None)
            self.update_vnf_fm_alarm.take_action(parsed_args)
            mock_req.assert_called_once_with(
                f'/vnffm/v1/alarms/{uuidsentinel.vnf_fm_alarm_id}',
                'PATCH', body=mock.ANY, headers=mock.ANY,
                content_type='application/merge-patch+json', accept='json')

    @ddt.data('ACKNOWLEDGED')
    def test_take_action_vnf_lcm_op_occ_id_not_found(self, ack_state):
        """Test if vnf-lcm-op-occ-id does not find"""

        arg_list = ['--ack-state', ack_state, uuidsentinel.vnf_fm_alarm_id]
        verify_list = [('ack_state', ack_state),
                       ('vnf_fm_alarm_id', uuidsentinel.vnf_fm_alarm_id)]

        # command param
        parsed_args = self.check_parser(
            self.update_vnf_fm_alarm, arg_list, verify_list)

        url = os.path.join(
            self.url, 'vnffm/v1/alarms', uuidsentinel.vnf_fm_alarm_id)

        self.requests_mock.register_uri(
            'PATCH', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.update_vnf_fm_alarm.take_action,
                          parsed_args)

    @ddt.data('UNACKNOWLEDGED')
    def test_take_action_vnf_lcm_op_occ_state_is_conflict(self, ack_state):
        """Test if vnf-lcm-op-occ state is conflict"""

        arg_list = ['--ack-state', ack_state, uuidsentinel.vnf_fm_alarm_id]
        verify_list = [('ack_state', ack_state),
                       ('vnf_fm_alarm_id', uuidsentinel.vnf_fm_alarm_id)]

        # command param
        parsed_args = self.check_parser(
            self.update_vnf_fm_alarm, arg_list, verify_list)

        url = os.path.join(
            self.url, 'vnffm/v1/alarms', uuidsentinel.vnf_fm_alarm_id)

        self.requests_mock.register_uri(
            'PATCH', url, headers=self.header, status_code=409, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.update_vnf_fm_alarm.take_action,
                          parsed_args)
