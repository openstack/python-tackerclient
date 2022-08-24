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
import sys

from io import StringIO
from oslo_utils.fixture import uuidsentinel
from unittest import mock

from tackerclient.common import exceptions
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.osc.v2.vnffm import vnffm_sub
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v2 import vnffm_sub_fakes


class TestVnfFmSub(base.FixturedTestCase):
    client_fixture_class = client.ClientFixture

    def setUp(self):
        super(TestVnfFmSub, self).setUp()
        self.url = client.TACKER_URL
        self.header = {'content-type': 'application/json'}
        self.app = mock.Mock()
        self.app_args = mock.Mock()
        self.client_manager = self.cs
        self.app.client_manager.tackerclient = self.client_manager


def _get_columns_vnffm_sub(action=None):
    columns = ['ID', 'Callback Uri']

    if action == 'show' or action == 'create':
        columns.extend(['Filter', 'Links'])

    return columns


@ddt.ddt
class TestCreateVnfFmSub(TestVnfFmSub):

    def setUp(self):
        super(TestCreateVnfFmSub, self).setUp()
        self.create_vnf_fm_sub = vnffm_sub.CreateVnfFmSub(
            self.app, self.app_args, cmd_name='vnffm sub create')

    def test_create_no_args(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.create_vnf_fm_sub, [], [])

    @ddt.unpack
    def test_take_action(self):

        param_file = ("./tackerclient/osc/v2/vnffm/samples/"
                      "create_vnf_fm_subscription_param_sample.json")

        arg_list = [param_file]
        verify_list = [('request_file', param_file)]

        parsed_args = self.check_parser(self.create_vnf_fm_sub, arg_list,
                                        verify_list)

        json = vnffm_sub_fakes.vnf_fm_sub_response()
        self.requests_mock.register_uri(
            'POST', os.path.join(self.url, 'vnffm/v1/subscriptions'),
            json=json, headers=self.header)

        actual_columns, data = (
            self.create_vnf_fm_sub.take_action(parsed_args))

        _, attributes = vnffm_sub._get_columns(json)

        self.assertCountEqual(_get_columns_vnffm_sub("create"),
                              actual_columns)
        self.assertListItemsEqual(vnffm_sub_fakes.get_vnffm_sub_data(
            json, columns=attributes), data)


class TestListVnfFmSub(TestVnfFmSub):

    def setUp(self):
        super(TestListVnfFmSub, self).setUp()
        self.list_vnffm_sub = vnffm_sub.ListVnfFmSub(
            self.app, self.app_args, cmd_name='vnffm sub list')

    def test_take_action(self):
        vnffm_subs_obj = vnffm_sub_fakes.create_vnf_fm_subs(
            count=3)
        parsed_args = self.check_parser(self.list_vnffm_sub, [], [])
        self.requests_mock.register_uri(
            'GET', os.path.join(self.url, 'vnffm/v1/subscriptions'),
            json=vnffm_subs_obj, headers=self.header)

        actual_columns, data = self.list_vnffm_sub.take_action(parsed_args)

        _, columns = tacker_osc_utils.get_column_definitions(
            vnffm_sub._ATTR_MAP, long_listing=True)

        expected_data = []
        for vnffm_sub_obj_idx in vnffm_subs_obj:
            expected_data.append(vnffm_sub_fakes.get_vnffm_sub_data(
                vnffm_sub_obj_idx, columns=columns))

        self.assertCountEqual(_get_columns_vnffm_sub(action='list'),
                              actual_columns)
        self.assertCountEqual(expected_data, list(data))

    def test_take_action_with_filter(self):
        vnffm_subs_obj = vnffm_sub_fakes.create_vnf_fm_subs(
            count=3)
        parsed_args = self.check_parser(
            self.list_vnffm_sub,
            ["--filter", '(eq,callbackUri,/nfvo/notify/alarm)'],
            [('filter', '(eq,callbackUri,/nfvo/notify/alarm)')])
        self.requests_mock.register_uri(
            'GET', os.path.join(
                self.url,
                'vnffm/v1/subscriptions?'
                'filter=(eq,callbackUri,/nfvo/notify/alarm)'),
            json=vnffm_subs_obj, headers=self.header)

        actual_columns, data = self.list_vnffm_sub.take_action(parsed_args)

        _, columns = tacker_osc_utils.get_column_definitions(
            vnffm_sub._ATTR_MAP, long_listing=True)

        expected_data = []
        for vnffm_sub_obj_idx in vnffm_subs_obj:
            expected_data.append(vnffm_sub_fakes.get_vnffm_sub_data(
                vnffm_sub_obj_idx, columns=columns))

        self.assertCountEqual(_get_columns_vnffm_sub(action='list'),
                              actual_columns)
        self.assertListItemsEqual(expected_data, list(data))

    def test_take_action_with_incorrect_filter(self):

        parsed_args = self.check_parser(
            self.list_vnffm_sub,
            ["--filter", '(callbackUri)'],
            [('filter', '(callbackUri)')])

        url = os.path.join(
            self.url,
            'vnffm/v1/subscriptions?filter=(callbackUri)')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=400, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.list_vnffm_sub.take_action,
                          parsed_args)

    def test_take_action_internal_server_error(self):

        parsed_args = self.check_parser(
            self.list_vnffm_sub,
            ["--filter", '(eq,callbackUri,/nfvo/notify/alarm)'],
            [('filter', '(eq,callbackUri,/nfvo/notify/alarm)')])

        url = os.path.join(
            self.url,
            'vnffm/v1/subscriptions?'
            'filter=(eq,callbackUri,/nfvo/notify/alarm)')
        self.requests_mock.register_uri(
            'POST', url, headers=self.header, status_code=500, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.list_vnffm_sub.take_action,
                          parsed_args)


class TestShowVnfFmSub(TestVnfFmSub):

    def setUp(self):
        super(TestShowVnfFmSub, self).setUp()
        self.show_vnf_fm_subs = vnffm_sub.ShowVnfFmSub(
            self.app, self.app_args, cmd_name='vnffm sub show')

    def test_take_action(self):
        """Test of take_action()"""
        vnffm_sub_obj = vnffm_sub_fakes.vnf_fm_sub_response()

        arg_list = [vnffm_sub_obj['id']]
        verify_list = [('vnf_fm_sub_id', vnffm_sub_obj['id'])]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_fm_subs, arg_list, verify_list)
        url = os.path.join(
            self.url,
            'vnffm/v1/subscriptions',
            vnffm_sub_obj['id'])

        self.requests_mock.register_uri(
            'GET', url, headers=self.header, json=vnffm_sub_obj)

        columns, _ = (self.show_vnf_fm_subs.take_action(parsed_args))

        self.assertCountEqual(_get_columns_vnffm_sub('show'),
                              columns)

    def test_take_action_vnf_fm_sub_id_not_found(self):
        """Test if vnf-lcm-op-occ-id does not find."""
        arg_list = [uuidsentinel.vnf_fm_sub_id]
        verify_list = [('vnf_fm_sub_id', uuidsentinel.vnf_fm_sub_id)]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_fm_subs, arg_list, verify_list)

        url = os.path.join(
            self.url,
            'vnffm/v1/subscriptions',
            uuidsentinel.vnf_fm_sub_id)
        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.show_vnf_fm_subs.take_action,
                          parsed_args)

    def test_take_action_internal_server_error(self):
        """Test for internal server error."""
        arg_list = [uuidsentinel.vnf_fm_sub_id]
        verify_list = [('vnf_fm_sub_id', uuidsentinel.vnf_fm_sub_id)]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_fm_subs, arg_list, verify_list)

        url = os.path.join(
            self.url,
            'vnffm/v1/subscriptions',
            uuidsentinel.vnf_fm_sub_id)
        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=500, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.show_vnf_fm_subs.take_action,
                          parsed_args)


class TestDeleteVnfFmSub(TestVnfFmSub):

    def setUp(self):
        super(TestDeleteVnfFmSub, self).setUp()
        self.delete_vnf_fm_sub = vnffm_sub.DeleteVnfFmSub(
            self.app, self.app_args, cmd_name='vnffm sub delete')

        # Vnf Fm subscription to delete
        self.vnf_fm_subs = vnffm_sub_fakes.create_vnf_fm_subs(count=3)

    def _mock_request_url_for_delete(self, index):
        url = os.path.join(self.url, 'vnffm/v1/subscriptions',
                           self.vnf_fm_subs[index]['id'])

        self.requests_mock.register_uri('DELETE', url,
                                        headers=self.header, json={})

    def test_delete_one_vnf_fm_sub(self):
        arg_list = [self.vnf_fm_subs[0]['id']]
        verify_list = [('vnf_fm_sub_id',
                       [self.vnf_fm_subs[0]['id']])]

        parsed_args = self.check_parser(self.delete_vnf_fm_sub, arg_list,
                                        verify_list)

        self._mock_request_url_for_delete(0)
        sys.stdout = buffer = StringIO()
        result = self.delete_vnf_fm_sub.take_action(parsed_args)
        self.assertIsNone(result)
        self.assertEqual(
            (f"VNF FM subscription '{self.vnf_fm_subs[0]['id']}' "
             f"deleted successfully"), buffer.getvalue().strip())

    def test_delete_multiple_vnf_fm_sub(self):
        arg_list = []
        for obj in self.vnf_fm_subs:
            arg_list.append(obj['id'])
        verify_list = [('vnf_fm_sub_id', arg_list)]
        parsed_args = self.check_parser(self.delete_vnf_fm_sub, arg_list,
                                        verify_list)
        for i in range(0, 3):
            self._mock_request_url_for_delete(i)
        sys.stdout = buffer = StringIO()
        result = self.delete_vnf_fm_sub.take_action(parsed_args)
        self.assertIsNone(result)
        self.assertEqual('All specified VNF FM subscriptions are deleted '
                         'successfully', buffer.getvalue().strip())

    def test_delete_multiple_vnf_fm_sub_exception(self):
        arg_list = [
            self.vnf_fm_subs[0]['id'],
            'xxxx-yyyy-zzzz',
            self.vnf_fm_subs[1]['id'],
        ]
        verify_list = [('vnf_fm_sub_id', arg_list)]
        parsed_args = self.check_parser(self.delete_vnf_fm_sub,
                                        arg_list, verify_list)

        self._mock_request_url_for_delete(0)

        url = os.path.join(self.url, 'vnffm/v1/subscriptions',
                           'xxxx-yyyy-zzzz')
        self.requests_mock.register_uri(
            'GET', url, exc=exceptions.ConnectionFailed)

        self._mock_request_url_for_delete(1)
        exception = self.assertRaises(exceptions.CommandError,
                                      self.delete_vnf_fm_sub.take_action,
                                      parsed_args)

        self.assertEqual('Failed to delete 1 of 3 VNF FM subscriptions.',
                         exception.message)
