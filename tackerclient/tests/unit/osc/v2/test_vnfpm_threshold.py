# Copyright (C) 2023 Fujitsu
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

from tackerclient import client as root_client
from tackerclient.common import exceptions
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.osc.v2.vnfpm import vnfpm_threshold
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v2 import vnfpm_threshold_fakes
from tackerclient.tests.unit.test_cli10 import MyResp
from tackerclient.v1_0 import client as proxy_client


class TestVnfPmThreshold(base.FixturedTestCase):
    client_fixture_class = client.ClientFixture

    def setUp(self):
        super(TestVnfPmThreshold, self).setUp()
        self.url = client.TACKER_URL
        self.header = {'content-type': 'application/json'}
        self.app = mock.Mock()
        self.app_args = mock.Mock()
        self.client_manager = self.cs
        self.app.client_manager.tackerclient = self.client_manager


def _get_columns_vnfpm_threshold(action=None):
    if action == 'update':
        columns = ['Callback Uri']
    else:
        columns = ['ID', 'Object Type', 'Object Instance Id',
                   'Sub Object Instance Ids', 'Criteria', 'Callback Uri',
                   'Links']
    if action == 'list':
        columns = [
            'ID', 'Object Type', 'Links'
        ]
    return columns


@ddt.ddt
class TestCreateVnfPmThreshold(TestVnfPmThreshold):

    def setUp(self):
        super(TestCreateVnfPmThreshold, self).setUp()
        self.create_vnf_pm_threshold = vnfpm_threshold.CreateVnfPmThreshold(
            self.app, self.app_args, cmd_name='vnfpm threshold create')

    def test_create_no_args(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.create_vnf_pm_threshold, [], [])

    @ddt.unpack
    def test_take_action(self):
        param_file = ("./tackerclient/osc/v2/vnfpm/samples/"
                      "create_vnf_pm_threshold_param_sample.json")

        arg_list = [param_file]
        verify_list = [('request_file', param_file)]

        parsed_args = self.check_parser(self.create_vnf_pm_threshold, arg_list,
                                        verify_list)

        response_json = vnfpm_threshold_fakes.vnf_pm_threshold_response()
        self.requests_mock.register_uri(
            'POST', os.path.join(self.url, 'vnfpm/v2/thresholds'),
            json=response_json, headers=self.header)

        actual_columns, data = (
            self.create_vnf_pm_threshold.take_action(parsed_args))
        self.assertCountEqual(_get_columns_vnfpm_threshold(),
                              actual_columns)

        _, attributes = vnfpm_threshold._get_columns(response_json)
        expected_data = vnfpm_threshold_fakes.get_vnfpm_threshold_data(
            response_json, columns=attributes)
        self.assertListItemsEqual(expected_data, data)


@ddt.ddt
class TestListVnfPmThreshold(TestVnfPmThreshold):

    def setUp(self):
        super(TestListVnfPmThreshold, self).setUp()
        self.list_vnf_pm_thresholds = vnfpm_threshold.ListVnfPmThreshold(
            self.app, self.app_args, cmd_name='vnfpm threshold list')

    def test_take_action(self):
        vnf_pm_threshold_objs = vnfpm_threshold_fakes.create_vnf_pm_thresholds(
            count=3)
        parsed_args = self.check_parser(self.list_vnf_pm_thresholds, [], [])
        self.requests_mock.register_uri(
            'GET',
            os.path.join(self.url, 'vnfpm/v2/thresholds'),
            json=vnf_pm_threshold_objs, headers=self.header)

        actual_columns, data = self.list_vnf_pm_thresholds.take_action(
            parsed_args)

        _, columns = tacker_osc_utils.get_column_definitions(
            vnfpm_threshold._ATTR_MAP, long_listing=True)

        expected_data = []
        for vnf_pm_threshold_obj_idx in vnf_pm_threshold_objs:
            expected_data.append(
                vnfpm_threshold_fakes.get_vnfpm_threshold_data(
                    vnf_pm_threshold_obj_idx, columns=columns))

        self.assertCountEqual(_get_columns_vnfpm_threshold(action='list'),
                              actual_columns)
        self.assertCountEqual(expected_data, list(data))

    def test_take_action_with_filter(self):
        vnf_pm_threshold_objs = vnfpm_threshold_fakes.create_vnf_pm_thresholds(
            count=3)
        parsed_args = self.check_parser(
            self.list_vnf_pm_thresholds,
            ["--filter", '(eq,perceivedSeverity,WARNING)'],
            [('filter', '(eq,perceivedSeverity,WARNING)')])
        self.requests_mock.register_uri(
            'GET', os.path.join(
                self.url,
                'vnfpm/v2/thresholds?filter=(eq,perceivedSeverity,WARNING)'),
            json=vnf_pm_threshold_objs, headers=self.header)

        actual_columns, data = self.list_vnf_pm_thresholds.take_action(
            parsed_args)

        _, columns = tacker_osc_utils.get_column_definitions(
            vnfpm_threshold._ATTR_MAP, long_listing=True)

        expected_data = []
        for vnf_pm_threshold_obj_idx in vnf_pm_threshold_objs:
            expected_data.append(
                vnfpm_threshold_fakes.get_vnfpm_threshold_data(
                    vnf_pm_threshold_obj_idx, columns=columns))

        self.assertCountEqual(_get_columns_vnfpm_threshold(action='list'),
                              actual_columns)
        self.assertListItemsEqual(expected_data, list(data))

    def test_take_action_with_incorrect_filter(self):
        parsed_args = self.check_parser(
            self.list_vnf_pm_thresholds,
            ["--filter", '(perceivedSeverity)'],
            [('filter', '(perceivedSeverity)')])

        url = os.path.join(
            self.url, 'vnfpm/v2/thresholds?filter=(perceivedSeverity)')

        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=400, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.list_vnf_pm_thresholds.take_action,
                          parsed_args)

    def test_take_action_internal_server_error(self):
        parsed_args = self.check_parser(
            self.list_vnf_pm_thresholds,
            ["--filter", '(eq,perceivedSeverity,WARNING)'],
            [('filter', '(eq,perceivedSeverity,WARNING)')])

        url = os.path.join(
            self.url,
            'vnfpm/v2/thresholds?filter=(eq,perceivedSeverity,WARNING)')

        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=500, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.list_vnf_pm_thresholds.take_action,
                          parsed_args)


class TestShowVnfPmThreshold(TestVnfPmThreshold):

    def setUp(self):
        super(TestShowVnfPmThreshold, self).setUp()
        self.show_vnf_pm_thresholds = vnfpm_threshold.ShowVnfPmThreshold(
            self.app, self.app_args, cmd_name='vnfpm threshold show')

    def test_take_action(self):
        vnfpm_threshold_obj = vnfpm_threshold_fakes.vnf_pm_threshold_response()

        arg_list = [vnfpm_threshold_obj['id']]
        verify_list = [('vnf_pm_threshold_id', vnfpm_threshold_obj['id'])]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_pm_thresholds, arg_list, verify_list)
        url = os.path.join(
            self.url, 'vnfpm/v2/thresholds', vnfpm_threshold_obj['id'])

        self.requests_mock.register_uri(
            'GET', url, headers=self.header, json=vnfpm_threshold_obj)

        columns, data = (self.show_vnf_pm_thresholds.take_action(parsed_args))

        self.assertCountEqual(_get_columns_vnfpm_threshold('show'), columns)

        _, attributes = vnfpm_threshold._get_columns(vnfpm_threshold_obj)
        self.assertListItemsEqual(
            vnfpm_threshold_fakes.get_vnfpm_threshold_data(
                vnfpm_threshold_obj, columns=attributes), data)

    def test_take_action_vnf_pm_threshold_id_not_found(self):
        arg_list = [uuidsentinel.vnf_pm_threshold_id]
        verify_list = [('vnf_pm_threshold_id',
                        uuidsentinel.vnf_pm_threshold_id)]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_pm_thresholds, arg_list, verify_list)

        url = os.path.join(
            self.url, 'vnfpm/v2/thresholds',
            uuidsentinel.vnf_pm_threshold_id)
        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.show_vnf_pm_thresholds.take_action,
                          parsed_args)

    def test_take_action_internal_server_error(self):
        arg_list = [uuidsentinel.vnf_pm_threshold_id]
        verify_list = [('vnf_pm_threshold_id',
                        uuidsentinel.vnf_pm_threshold_id)]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_pm_thresholds, arg_list, verify_list)

        url = os.path.join(
            self.url, 'vnfpm/v2/thresholds',
            uuidsentinel.vnf_pm_threshold_id)
        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=500, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.show_vnf_pm_thresholds.take_action,
                          parsed_args)


@ddt.ddt
class TestUpdateVnfPmThreshold(TestVnfPmThreshold):

    def setUp(self):
        super(TestUpdateVnfPmThreshold, self).setUp()
        self.update_vnf_pm_threshold = vnfpm_threshold.UpdateVnfPmThreshold(
            self.app, self.app_args, cmd_name='vnfpm threshold update')

    def test_take_action(self):
        param_file = ("./tackerclient/osc/v2/vnfpm/samples/"
                      "update_vnf_pm_threshold_param_sample.json")
        arg_list = [uuidsentinel.vnf_pm_threshold_id, param_file]
        verify_list = [
            ('vnf_pm_threshold_id', uuidsentinel.vnf_pm_threshold_id),
            ('request_file', param_file)
        ]
        vnfpm_threshold_obj = vnfpm_threshold_fakes.vnf_pm_threshold_response(
            None, 'update')

        # command param
        parsed_args = self.check_parser(
            self.update_vnf_pm_threshold, arg_list, verify_list)
        url = os.path.join(
            self.url, 'vnfpm/v2/thresholds',
            uuidsentinel.vnf_pm_threshold_id)
        self.requests_mock.register_uri(
            'PATCH', url, headers=self.header, json=vnfpm_threshold_obj)

        actual_columns, data = (
            self.update_vnf_pm_threshold.take_action(parsed_args))
        expected_columns = _get_columns_vnfpm_threshold(action='update')
        self.assertCountEqual(expected_columns, actual_columns)

        _, columns = vnfpm_threshold._get_columns(
            vnfpm_threshold_obj, action='update')
        expected_data = vnfpm_threshold_fakes.get_vnfpm_threshold_data(
            vnfpm_threshold_obj, columns=columns)
        self.assertEqual(expected_data, data)

    @mock.patch.object(proxy_client.ClientBase, 'deserialize')
    def test_take_action_check_content_type(self, mock_des):
        param_file = ('./tackerclient/osc/v2/vnfpm/samples/'
                      'update_vnf_pm_threshold_param_sample.json')
        arg_list = [uuidsentinel.vnf_pm_threshold_id, param_file]
        verify_list = [
            ('vnf_pm_threshold_id', uuidsentinel.vnf_pm_threshold_id),
            ('request_file', param_file)
        ]
        vnfpm_threshold_obj = vnfpm_threshold_fakes.vnf_pm_threshold_response(
            None, 'update')
        mock_des.return_value = {}

        # command param
        parsed_args = self.check_parser(
            self.update_vnf_pm_threshold, arg_list, verify_list)
        url = os.path.join(
            self.url, 'vnfpm/v2/thresholds',
            uuidsentinel.vnf_pm_threshold_id)
        self.requests_mock.register_uri(
            'PATCH', url, headers=self.header, json=vnfpm_threshold_obj)

        with mock.patch.object(root_client.HTTPClient,
                               'do_request') as mock_req:
            headers = {'Content-Type': 'application/json'}
            mock_req.return_value = (MyResp(200, headers=headers), None)
            self.update_vnf_pm_threshold.take_action(parsed_args)
            mock_req.assert_called_once_with(
                f'/vnfpm/v2/thresholds/{uuidsentinel.vnf_pm_threshold_id}',
                'PATCH', body=mock.ANY, headers=mock.ANY,
                content_type='application/merge-patch+json', accept='json')

    def test_take_action_vnf_pm_threshold_id_not_found(self):
        param_file = ("./tackerclient/osc/v2/vnfpm/samples/"
                      "update_vnf_pm_threshold_param_sample.json")
        arg_list = [uuidsentinel.vnf_pm_threshold_id, param_file]
        verify_list = [
            ('vnf_pm_threshold_id', uuidsentinel.vnf_pm_threshold_id),
            ('request_file', param_file)
        ]

        # command param
        parsed_args = self.check_parser(
            self.update_vnf_pm_threshold, arg_list, verify_list)
        url = os.path.join(
            self.url, 'vnfpm/v2/thresholds',
            uuidsentinel.vnf_pm_threshold_id)
        self.requests_mock.register_uri(
            'PATCH', url, headers=self.header, status_code=404, json={})
        self.assertRaises(exceptions.TackerClientException,
                          self.update_vnf_pm_threshold.take_action,
                          parsed_args)


class TestDeleteVnfPmThreshold(TestVnfPmThreshold):

    def setUp(self):
        super(TestDeleteVnfPmThreshold, self).setUp()
        self.delete_vnf_pm_threshold = vnfpm_threshold.DeleteVnfPmThreshold(
            self.app, self.app_args, cmd_name='vnfpm threshold delete')

        # Vnf Pm threshold to delete
        self.vnf_pm_thresholds = (
            vnfpm_threshold_fakes.create_vnf_pm_thresholds(count=3))

    def _mock_request_url_for_delete(self, index):
        url = os.path.join(self.url, 'vnfpm/v2/thresholds',
                           self.vnf_pm_thresholds[index]['id'])

        self.requests_mock.register_uri('DELETE', url,
                                        headers=self.header, json={})

    def test_delete_one_vnf_pm_threshold(self):
        arg_list = [self.vnf_pm_thresholds[0]['id']]
        verify_list = [('vnf_pm_threshold_id',
                       [self.vnf_pm_thresholds[0]['id']])]

        parsed_args = self.check_parser(self.delete_vnf_pm_threshold, arg_list,
                                        verify_list)

        self._mock_request_url_for_delete(0)
        sys.stdout = buffer = StringIO()
        result = self.delete_vnf_pm_threshold.take_action(parsed_args)
        self.assertIsNone(result)
        self.assertEqual(
            (f"VNF PM threshold '{self.vnf_pm_thresholds[0]['id']}' "
             f"deleted successfully"), buffer.getvalue().strip())

    def test_delete_multiple_vnf_pm_threshold(self):
        arg_list = []
        for obj in self.vnf_pm_thresholds:
            arg_list.append(obj['id'])
        verify_list = [('vnf_pm_threshold_id', arg_list)]
        parsed_args = self.check_parser(self.delete_vnf_pm_threshold, arg_list,
                                        verify_list)
        for i in range(0, len(self.vnf_pm_thresholds)):
            self._mock_request_url_for_delete(i)
        sys.stdout = buffer = StringIO()
        result = self.delete_vnf_pm_threshold.take_action(parsed_args)
        self.assertIsNone(result)
        self.assertEqual('All specified VNF PM thresholds are deleted '
                         'successfully', buffer.getvalue().strip())

    def test_delete_multiple_vnf_pm_threshold_exception(self):
        arg_list = [
            self.vnf_pm_thresholds[0]['id'],
            'xxxx-yyyy-zzzz',
            self.vnf_pm_thresholds[1]['id'],
        ]
        verify_list = [('vnf_pm_threshold_id', arg_list)]
        parsed_args = self.check_parser(self.delete_vnf_pm_threshold,
                                        arg_list, verify_list)

        self._mock_request_url_for_delete(0)

        url = os.path.join(self.url, 'vnfpm/v2/thresholds',
                           'xxxx-yyyy-zzzz')
        self.requests_mock.register_uri(
            'GET', url, exc=exceptions.ConnectionFailed)

        self._mock_request_url_for_delete(1)
        exception = self.assertRaises(exceptions.CommandError,
                                      self.delete_vnf_pm_threshold.take_action,
                                      parsed_args)

        self.assertEqual(
            f'Failed to delete 1 of {len(self.vnf_pm_thresholds)} '
            'VNF PM thresholds.', exception.message)
