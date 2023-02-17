# Copyright (C) 2022 Nippon Telegraph and Telephone Corporation
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

import copy
import os
import sys

from io import StringIO
from tackerclient.common import exceptions
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.osc.v1.vnflcm import vnflcm_subsc
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1 import test_vnflcm
from tackerclient.tests.unit.osc.v1 import vnflcm_subsc_fakes


def _get_columns_vnflcm_subsc(action=None):
    columns = ['ID', 'Filter', 'Callback URI', 'Links']
    if action == 'list':
        columns = [ele for ele in columns if ele not in
                   ['Filter', 'Links']]
    return columns


class TestCreateLccnSubscription(test_vnflcm.TestVnfLcm):

    def setUp(self):
        super(TestCreateLccnSubscription, self).setUp()
        self.create_subscription = vnflcm_subsc.CreateLccnSubscription(
            self.app, self.app_args, cmd_name='vnflcm subsc create')

    def test_create_no_args(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.create_subscription, [], [])

    def test_take_action(self):
        subscription = vnflcm_subsc_fakes.lccn_subsc_response()
        sample_param_file = ("./tackerclient/osc/v1/vnflcm/samples/"
                             "create_lccn_subscription_param_sample.json")

        arglist = [sample_param_file]
        verifylist = [('create_request_file', sample_param_file)]

        # command param
        parsed_args = self.check_parser(self.create_subscription,
                                        arglist, verifylist)

        self.requests_mock.register_uri(
            'POST', os.path.join(self.url, 'vnflcm/v1/subscriptions'),
            json=subscription, headers=self.header)

        actual_columns, data = (self.create_subscription.take_action(
                                parsed_args))

        headers, attributes = vnflcm_subsc._get_columns(subscription)

        self.assertCountEqual(_get_columns_vnflcm_subsc(),
                              actual_columns)
        self.assertListItemsEqual(vnflcm_subsc_fakes.get_subscription_data(
            subscription, columns=attributes), data)


class TestListLccnSubscription(test_vnflcm.TestVnfLcm):

    def setUp(self):
        super(TestListLccnSubscription, self).setUp()
        self.list_subscription = vnflcm_subsc.ListLccnSubscription(
            self.app, self.app_args, cmd_name='vnflcm subsc list')

    def test_take_action(self):
        subscriptions = vnflcm_subsc_fakes.create_subscriptions(count=3)
        parsed_args = self.check_parser(self.list_subscription, [], [])
        self.requests_mock.register_uri(
            'GET', os.path.join(self.url, 'vnflcm/v1/subscriptions'),
            json=subscriptions, headers=self.header)
        actual_columns, data = self.list_subscription.take_action(parsed_args)

        headers, columns = tacker_osc_utils.get_column_definitions(
            self.list_subscription.get_attributes(), long_listing=True)

        expected_data = []
        for subscription_obj in subscriptions:
            expected_data.append(vnflcm_subsc_fakes.get_subscription_data(
                subscription_obj, columns=columns, list_action=True))

        self.assertCountEqual(_get_columns_vnflcm_subsc(action='list'),
                              actual_columns)
        self.assertCountEqual(expected_data, list(data))

    def test_take_action_with_pagination(self):
        subscriptions = vnflcm_subsc_fakes.create_subscriptions(count=3)
        next_links_num = 3
        path = os.path.join(self.url, 'vnflcm/v1/subscriptions')
        parsed_args = self.check_parser(self.list_subscription, [], [])

        links = [0] * next_links_num
        link_headers = [0] * next_links_num

        for i in range(next_links_num):
            links[i] = (
                '{base_url}?nextpage_opaque_marker={subscription_id}'.format(
                    base_url=path,
                    subscription_id=subscriptions[i]['id']))

            link_headers[i] = copy.deepcopy(self.header)
            link_headers[i]['Link'] = '<{link_url}>; rel="next"'.format(
                link_url=links[i])

        self.requests_mock.register_uri(
            'GET', path, json=[subscriptions[0]], headers=link_headers[0])
        self.requests_mock.register_uri(
            'GET', links[0], json=[subscriptions[1]],
            headers=link_headers[1])
        self.requests_mock.register_uri(
            'GET', links[1], json=[subscriptions[2]],
            headers=link_headers[2])
        self.requests_mock.register_uri(
            'GET', links[2], json=[], headers=self.header)

        actual_columns, data = self.list_subscription.take_action(parsed_args)

        headers, columns = tacker_osc_utils.get_column_definitions(
            self.list_subscription.get_attributes(), long_listing=True)

        expected_data = []
        for subscription_obj in subscriptions:
            expected_data.append(vnflcm_subsc_fakes.get_subscription_data(
                subscription_obj, columns=columns, list_action=True))

        self.assertCountEqual(_get_columns_vnflcm_subsc(action='list'),
                              actual_columns)

        self.assertCountEqual(expected_data, list(data))


class TestShowLccnSubscription(test_vnflcm.TestVnfLcm):

    def setUp(self):
        super(TestShowLccnSubscription, self).setUp()
        self.show_subscription = vnflcm_subsc.ShowLccnSubscription(
            self.app, self.app_args, cmd_name='vnflcm subsc show')

    def test_take_action(self):
        subscription = vnflcm_subsc_fakes.lccn_subsc_response()

        arglist = [subscription['id']]
        verifylist = [('subscription_id', subscription['id'])]

        # command param
        parsed_args = self.check_parser(self.show_subscription, arglist,
                                        verifylist)

        self.requests_mock.register_uri(
            'GET', os.path.join(self.url, 'vnflcm/v1/subscriptions',
                                subscription['id']),
            json=subscription, headers=self.header)

        columns, data = (self.show_subscription.take_action(parsed_args))
        self.assertCountEqual(_get_columns_vnflcm_subsc(),
                              columns)
        headers, attributes = vnflcm_subsc._get_columns(subscription)
        self.assertListItemsEqual(
            vnflcm_subsc_fakes.get_subscription_data(subscription,
                                                     columns=attributes),
            data)


class TestDeleteLccnSubscription(test_vnflcm.TestVnfLcm):

    subscriptions = vnflcm_subsc_fakes.create_subscriptions(count=3)

    def setUp(self):
        super(TestDeleteLccnSubscription, self).setUp()
        self.delete_subscription = vnflcm_subsc.DeleteLccnSubscription(
            self.app, self.app_args, cmd_name='vnflcm subsc delete')

    def _mock_request_url_for_delete(self, subsc_index):
        url = os.path.join(self.url, 'vnflcm/v1/subscriptions',
                           self.subscriptions[subsc_index]['id'])

        json = self.subscriptions[subsc_index]

        self.requests_mock.register_uri('GET', url, json=json,
                                        headers=self.header)
        self.requests_mock.register_uri('DELETE', url,
                                        headers=self.header, json={})

    def test_delete_one_subscription(self):
        arglist = [self.subscriptions[0]['id']]
        verifylist = [('subscription_id',
                       [self.subscriptions[0]['id']])]

        parsed_args = self.check_parser(self.delete_subscription,
                                        arglist, verifylist)

        self._mock_request_url_for_delete(0)
        sys.stdout = buffer = StringIO()
        result = self.delete_subscription.take_action(parsed_args)
        self.assertIsNone(result)
        self.assertEqual(("Lccn Subscription '%s' is deleted successfully")
                         % self.subscriptions[0]['id'],
                         buffer.getvalue().strip())

    def test_delete_multiple_subscription(self):
        arglist = []
        for subscription in self.subscriptions:
            arglist.append(subscription['id'])
        verifylist = [('subscription_id', arglist)]
        parsed_args = self.check_parser(self.delete_subscription,
                                        arglist, verifylist)
        for i in range(0, 3):
            self._mock_request_url_for_delete(i)
        sys.stdout = buffer = StringIO()
        result = self.delete_subscription.take_action(parsed_args)
        self.assertIsNone(result)
        self.assertEqual('All specified Lccn Subscriptions are deleted '
                         'successfully', buffer.getvalue().strip())

    def test_delete_multiple_subscription_exception(self):
        arglist = [
            self.subscriptions[0]['id'],
            'xxxx-yyyy-zzzz',
            self.subscriptions[1]['id'],
        ]
        verifylist = [('subscription_id', arglist)]
        parsed_args = self.check_parser(self.delete_subscription,
                                        arglist, verifylist)

        self._mock_request_url_for_delete(0)

        url = os.path.join(self.url, 'vnflcm/v1/subscriptions',
                           'xxxx-yyyy-zzzz')
        self.requests_mock.register_uri(
            'GET', url, exc=exceptions.ConnectionFailed)

        self._mock_request_url_for_delete(1)
        exception = self.assertRaises(exceptions.CommandError,
                                      self.delete_subscription.take_action,
                                      parsed_args)

        self.assertEqual('Failed to delete 1 of 3 Lccn Subscriptions.',
                         exception.message)
