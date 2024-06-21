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

from tackerclient import client as root_client
from tackerclient.common import exceptions
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.osc.v2.vnfpm import vnfpm_job
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v2 import vnfpm_job_fakes
from tackerclient.tests.unit.test_cli10 import MyResp
from tackerclient.v1_0 import client as proxy_client


class TestVnfPmJob(base.FixturedTestCase):
    client_fixture_class = client.ClientFixture

    def setUp(self):
        super(TestVnfPmJob, self).setUp()
        self.url = client.TACKER_URL
        self.header = {'content-type': 'application/json'}
        self.app = mock.Mock()
        self.app_args = mock.Mock()
        self.client_manager = self.cs
        self.app.client_manager.tackerclient = self.client_manager


def _get_columns_vnfpm_job(action=None):
    if action == 'update':
        columns = ['Callback Uri']
    else:
        columns = ['ID', 'Object Type', 'Object Instance Ids',
                   'Sub Object Instance Ids', 'Criteria', 'Callback Uri',
                   'Reports', 'Links']
    if action == 'list':
        columns = [
            ele for ele in columns if ele not in [
                'Criteria', 'Sub Object Instance Ids', 'Reports', 'Links'
            ]
        ]
    return columns


@ddt.ddt
class TestCreateVnfPmJob(TestVnfPmJob):

    def setUp(self):
        super(TestCreateVnfPmJob, self).setUp()
        self.create_vnf_pm_job = vnfpm_job.CreateVnfPmJob(
            self.app, self.app_args, cmd_name='vnfpm job create')

    def test_create_no_args(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.create_vnf_pm_job, [], [])

    @ddt.unpack
    def test_take_action(self):
        param_file = ("./tackerclient/osc/v2/vnfpm/samples/"
                      "create_vnf_pm_job_param_sample.json")

        arg_list = [param_file]
        verify_list = [('request_file', param_file)]

        parsed_args = self.check_parser(self.create_vnf_pm_job, arg_list,
                                        verify_list)

        json = vnfpm_job_fakes.vnf_pm_job_response()
        self.requests_mock.register_uri(
            'POST', os.path.join(self.url, 'vnfpm/v2/pm_jobs'),
            json=json, headers=self.header)

        actual_columns, data = (
            self.create_vnf_pm_job.take_action(parsed_args))
        self.assertCountEqual(_get_columns_vnfpm_job(),
                              actual_columns)

        _, attributes = vnfpm_job._get_columns(json)
        expected_data = vnfpm_job_fakes.get_vnfpm_job_data(
            json, columns=attributes)
        self.assertListItemsEqual(expected_data, data)


@ddt.ddt
class TestListVnfPmJob(TestVnfPmJob):

    def setUp(self):
        super(TestListVnfPmJob, self).setUp()
        self.list_vnf_pm_jobs = vnfpm_job.ListVnfPmJob(
            self.app, self.app_args, cmd_name='vnfpm job list')
        self._vnf_pm_jobs = self._get_vnf_pm_jobs()

    def _get_vnf_pm_jobs(self):
        return vnfpm_job_fakes.create_vnf_pm_jobs(count=3)

    def get_list_columns(self, all_fields=False, exclude_fields=None,
                         extra_fields=None, exclude_default=False):

        columns = ['Id', 'Object Type', 'Links']
        complex_columns = [
            'Object Instance Ids',
            'Sub Object Instance Ids',
            'Criteria',
            'Reports'
        ]
        simple_columns = ['Callback Uri']

        if extra_fields:
            columns.extend(extra_fields)

        if exclude_fields:
            columns.extend([field for field in complex_columns
                           if field not in exclude_fields])
        if all_fields:
            columns.extend(complex_columns)
            columns.extend(simple_columns)

        if exclude_default:
            columns.extend(simple_columns)

        return columns

    def _get_mock_response_for_list_vnf_pm_jobs(
            self, filter_attribute, json=None):
        self.requests_mock.register_uri(
            'GET', self.url + '/vnfpm/v2/pm_jobs?' + filter_attribute,
            json=json if json else self._get_vnf_pm_jobs(),
            headers=self.header)

    def test_take_action_default_fields(self):
        parsed_args = self.check_parser(self.list_vnf_pm_jobs, [], [])
        self.requests_mock.register_uri(
            'GET', self.url + '/vnfpm/v2/pm_jobs',
            json=self._vnf_pm_jobs, headers=self.header)
        actual_columns, data = self.list_vnf_pm_jobs.take_action(parsed_args)
        expected_data = []
        _, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnf_pm_jobs.get_attributes(), long_listing=True)

        for vnf_pm_job_obj in self._vnf_pm_jobs['vnf_pm_jobs']:
            expected_data.append(vnfpm_job_fakes.get_vnfpm_job_data(
                vnf_pm_job_obj, columns=columns))
        self.assertCountEqual(self.get_list_columns(), actual_columns)
        self.assertListItemsEqual(expected_data, list(data))

    @ddt.data('all_fields', 'exclude_default')
    def test_take_action(self, arg):
        parsed_args = self.check_parser(
            self.list_vnf_pm_jobs,
            ["--" + arg, "--filter", '(eq,objectType,VNFC)'],
            [(arg, True), ('filter', '(eq,objectType,VNFC)')])
        vnf_pm_jobs = self._get_vnf_pm_jobs()
        self._get_mock_response_for_list_vnf_pm_jobs(
            'filter=(eq,objectType,VNFC)&' + arg, json=vnf_pm_jobs)

        actual_columns, data = self.list_vnf_pm_jobs.take_action(parsed_args)
        expected_data = []
        kwargs = {arg: True}
        _, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnf_pm_jobs.get_attributes(**kwargs), long_listing=True)

        for vnf_pm_job_obj in vnf_pm_jobs['vnf_pm_jobs']:
            expected_data.append(vnfpm_job_fakes.get_vnfpm_job_data(
                vnf_pm_job_obj, columns=columns))

        self.assertCountEqual(self.get_list_columns(**kwargs), actual_columns)
        self.assertListItemsEqual(expected_data, list(data))

    def test_take_action_with_exclude_fields(self):
        parsed_args = self.check_parser(
            self.list_vnf_pm_jobs,
            ["--exclude_fields", 'objectInstanceIds,criteria',
             "--filter", '(eq,objectType,VNFC)'],
            [('exclude_fields', 'objectInstanceIds,criteria'),
             ('filter', '(eq,objectType,VNFC)')])
        vnf_pm_jobs = self._get_vnf_pm_jobs()
        updated_vnf_pm_jobs = {'vnf_pm_jobs': []}
        for vnf_pm_job_obj in vnf_pm_jobs['vnf_pm_jobs']:
            vnf_pm_job_obj.pop('objectInstanceIds')
            vnf_pm_job_obj.pop('criteria')
            updated_vnf_pm_jobs['vnf_pm_jobs'].append(vnf_pm_job_obj)
        self._get_mock_response_for_list_vnf_pm_jobs(
            'filter=(eq,objectType,VNFC)&'
            'exclude_fields=objectInstanceIds,criteria',
            json=updated_vnf_pm_jobs)

        actual_columns, data = self.list_vnf_pm_jobs.take_action(parsed_args)
        expected_data = []
        _, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnf_pm_jobs.get_attributes(
                exclude_fields=['objectInstanceIds', 'criteria']),
            long_listing=True)

        for updated_vnf_pm_obj in updated_vnf_pm_jobs['vnf_pm_jobs']:
            expected_data.append(vnfpm_job_fakes.get_vnfpm_job_data(
                updated_vnf_pm_obj, columns=columns))
        expected_columns = self.get_list_columns(
            exclude_fields=['Object Instance Ids', 'Criteria'])
        self.assertCountEqual(expected_columns, actual_columns)
        self.assertListItemsEqual(expected_data, list(data))

    @ddt.data((['--all_fields', '--fields', 'objectInstanceIds'],
               [('all_fields', True), ('fields', 'objectInstanceIds')]),
              (['--all_fields', '--exclude_fields', 'criteria'],
               [('all_fields', True), ('exclude_fields', 'criteria')]),
              (['--fields', 'objectInstanceIds',
                '--exclude_fields', 'criteria'],
               [('fields', 'objectInstanceIds'),
                ('exclude_fields', 'criteria')]))
    @ddt.unpack
    def test_take_action_with_invalid_combination(self, arglist, verifylist):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.list_vnf_pm_jobs, arglist, verifylist)

    def test_take_action_with_valid_combination(self):
        parsed_args = self.check_parser(
            self.list_vnf_pm_jobs,
            [
                "--fields", 'subObjectInstanceIds,criteria',
                "--exclude_default"
            ],
            [
                ('fields', 'subObjectInstanceIds,criteria'),
                ('exclude_default', True)
            ])
        vnf_pm_jobs = self._get_vnf_pm_jobs()

        updated_vnf_pm_jobs = {'vnf_pm_jobs': []}
        for vnf_pm_job_obj in vnf_pm_jobs['vnf_pm_jobs']:
            # vnf_pm_job_obj.pop('userDefinedData')
            updated_vnf_pm_jobs['vnf_pm_jobs'].append(vnf_pm_job_obj)

        self._get_mock_response_for_list_vnf_pm_jobs(
            'exclude_default&fields=subObjectInstanceIds,criteria',
            json=updated_vnf_pm_jobs)

        actual_columns, data = self.list_vnf_pm_jobs.take_action(parsed_args)
        expected_data = []
        _, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnf_pm_jobs.get_attributes(
                extra_fields=['subObjectInstanceIds', 'criteria'],
                exclude_default=True),
            long_listing=True)

        for updated_vnf_pm_job_obj in updated_vnf_pm_jobs['vnf_pm_jobs']:
            expected_data.append(vnfpm_job_fakes.get_vnfpm_job_data(
                updated_vnf_pm_job_obj, columns=columns))

        expected_columns = self.get_list_columns(
            extra_fields=['Sub Object Instance Ids', 'Criteria'],
            exclude_default=True)
        self.assertCountEqual(expected_columns, actual_columns)
        self.assertListItemsEqual(expected_data, list(data))


class TestShowVnfPmJob(TestVnfPmJob):

    def setUp(self):
        super(TestShowVnfPmJob, self).setUp()
        self.show_vnf_pm_jobs = vnfpm_job.ShowVnfPmJob(
            self.app, self.app_args, cmd_name='vnfpm job show')

    def test_take_action(self):
        """Test of take_action()"""
        vnfpm_job_obj = vnfpm_job_fakes.vnf_pm_job_response()

        arg_list = [vnfpm_job_obj['id']]
        verify_list = [('vnf_pm_job_id', vnfpm_job_obj['id'])]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_pm_jobs, arg_list, verify_list)
        url = os.path.join(
            self.url, 'vnfpm/v2/pm_jobs', vnfpm_job_obj['id'])

        self.requests_mock.register_uri(
            'GET', url, headers=self.header, json=vnfpm_job_obj)

        columns, data = (self.show_vnf_pm_jobs.take_action(parsed_args))

        self.assertCountEqual(_get_columns_vnfpm_job('show'), columns)

        _, attributes = vnfpm_job._get_columns(vnfpm_job_obj)
        self.assertListItemsEqual(
            vnfpm_job_fakes.get_vnfpm_job_data(
                vnfpm_job_obj, columns=attributes), data)

    def test_take_action_vnf_pm_job_id_not_found(self):
        """Test if vnf-pm-job-id does not find."""
        arg_list = [uuidsentinel.vnf_pm_job_id]
        verify_list = [('vnf_pm_job_id', uuidsentinel.vnf_pm_job_id)]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_pm_jobs, arg_list, verify_list)

        url = os.path.join(
            self.url, 'vnfpm/v2/pm_jobs', uuidsentinel.vnf_pm_job_id)
        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.show_vnf_pm_jobs.take_action,
                          parsed_args)

    def test_take_action_internal_server_error(self):
        """Test for internal server error."""
        arg_list = [uuidsentinel.vnf_pm_job_id]
        verify_list = [('vnf_pm_job_id', uuidsentinel.vnf_pm_job_id)]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_pm_jobs, arg_list, verify_list)

        url = os.path.join(
            self.url, 'vnfpm/v2/pm_jobs', uuidsentinel.vnf_pm_job_id)
        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=500, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.show_vnf_pm_jobs.take_action,
                          parsed_args)


@ddt.ddt
class TestUpdateVnfPmJob(TestVnfPmJob):

    def setUp(self):
        super(TestUpdateVnfPmJob, self).setUp()
        self.update_vnf_pm_job = vnfpm_job.UpdateVnfPmJob(
            self.app, self.app_args, cmd_name='vnfpm job update')

    def test_take_action(self):
        """Test of take_action()"""

        param_file = ("./tackerclient/osc/v2/vnfpm/samples/"
                      "update_vnf_pm_job_param_sample.json")
        arg_list = [uuidsentinel.vnf_pm_job_id, param_file]
        verify_list = [
            ('vnf_pm_job_id', uuidsentinel.vnf_pm_job_id),
            ('request_file', param_file)
        ]
        vnfpm_job_obj = vnfpm_job_fakes.vnf_pm_job_response(
            None, 'update')

        # command param
        parsed_args = self.check_parser(
            self.update_vnf_pm_job, arg_list, verify_list)
        url = os.path.join(
            self.url, 'vnfpm/v2/pm_jobs', uuidsentinel.vnf_pm_job_id)
        self.requests_mock.register_uri(
            'PATCH', url, headers=self.header, json=vnfpm_job_obj)

        actual_columns, data = (
            self.update_vnf_pm_job.take_action(parsed_args))
        expected_columns = _get_columns_vnfpm_job(action='update')
        self.assertCountEqual(expected_columns, actual_columns)

        _, columns = vnfpm_job._get_columns(
            vnfpm_job_obj, action='update')
        expected_data = vnfpm_job_fakes.get_vnfpm_job_data(
            vnfpm_job_obj, columns=columns)
        self.assertEqual(expected_data, data)

    @mock.patch.object(proxy_client.ClientBase, 'deserialize')
    def test_take_action_check_content_type(self, mock_des):
        """Check content type by test of take_action()"""

        param_file = ('./tackerclient/osc/v2/vnfpm/samples/'
                      'update_vnf_pm_job_param_sample.json')
        arg_list = [uuidsentinel.vnf_pm_job_id, param_file]
        verify_list = [
            ('vnf_pm_job_id', uuidsentinel.vnf_pm_job_id),
            ('request_file', param_file)
        ]
        vnfpm_job_obj = vnfpm_job_fakes.vnf_pm_job_response(
            None, 'update')
        mock_des.return_value = {}

        # command param
        parsed_args = self.check_parser(
            self.update_vnf_pm_job, arg_list, verify_list)
        url = os.path.join(
            self.url, 'vnfpm/v2/pm_jobs', uuidsentinel.vnf_pm_job_id)
        self.requests_mock.register_uri(
            'PATCH', url, headers=self.header, json=vnfpm_job_obj)

        with mock.patch.object(root_client.HTTPClient,
                               'do_request') as mock_req:
            headers = {'Content-Type': 'application/json'}
            mock_req.return_value = (MyResp(200, headers=headers), None)
            self.update_vnf_pm_job.take_action(parsed_args)
            mock_req.assert_called_once_with(
                f'/vnfpm/v2/pm_jobs/{uuidsentinel.vnf_pm_job_id}', 'PATCH',
                body=mock.ANY, headers=mock.ANY,
                content_type='application/merge-patch+json', accept='json')

    def test_take_action_vnf_pm_job_id_not_found(self):
        """Test if vnf-pm-job-id does not find"""

        param_file = ("./tackerclient/osc/v2/vnfpm/samples/"
                      "update_vnf_pm_job_param_sample.json")
        arg_list = [uuidsentinel.vnf_pm_job_id, param_file]
        verify_list = [
            ('vnf_pm_job_id', uuidsentinel.vnf_pm_job_id),
            ('request_file', param_file)
        ]

        # command param
        parsed_args = self.check_parser(
            self.update_vnf_pm_job, arg_list, verify_list)
        url = os.path.join(
            self.url, 'vnfpm/v2/pm_jobs', uuidsentinel.vnf_pm_job_id)
        self.requests_mock.register_uri(
            'PATCH', url, headers=self.header, status_code=404, json={})
        self.assertRaises(exceptions.TackerClientException,
                          self.update_vnf_pm_job.take_action,
                          parsed_args)


class TestDeleteVnfPmJob(TestVnfPmJob):

    def setUp(self):
        super(TestDeleteVnfPmJob, self).setUp()
        self.delete_vnf_pm_job = vnfpm_job.DeleteVnfPmJob(
            self.app, self.app_args, cmd_name='vnfpm job delete')

        # Vnf Fm job to delete
        self.vnf_pm_jobs = vnfpm_job_fakes.create_vnf_pm_jobs(
            count=3)['vnf_pm_jobs']

    def _mock_request_url_for_delete(self, index):
        url = os.path.join(self.url, 'vnfpm/v2/pm_jobs',
                           self.vnf_pm_jobs[index]['id'])

        self.requests_mock.register_uri('DELETE', url,
                                        headers=self.header, json={})

    def test_delete_one_vnf_pm_job(self):
        arg_list = [self.vnf_pm_jobs[0]['id']]
        verify_list = [('vnf_pm_job_id',
                       [self.vnf_pm_jobs[0]['id']])]

        parsed_args = self.check_parser(self.delete_vnf_pm_job, arg_list,
                                        verify_list)

        self._mock_request_url_for_delete(0)
        sys.stdout = buffer = StringIO()
        result = self.delete_vnf_pm_job.take_action(parsed_args)
        self.assertIsNone(result)
        self.assertEqual(
            (f"VNF PM job '{self.vnf_pm_jobs[0]['id']}' "
             f"deleted successfully"), buffer.getvalue().strip())

    def test_delete_multiple_vnf_pm_job(self):
        arg_list = []
        for obj in self.vnf_pm_jobs:
            arg_list.append(obj['id'])
        verify_list = [('vnf_pm_job_id', arg_list)]
        parsed_args = self.check_parser(self.delete_vnf_pm_job, arg_list,
                                        verify_list)
        for i in range(0, 3):
            self._mock_request_url_for_delete(i)
        sys.stdout = buffer = StringIO()
        result = self.delete_vnf_pm_job.take_action(parsed_args)
        self.assertIsNone(result)
        self.assertEqual('All specified VNF PM jobs are deleted '
                         'successfully', buffer.getvalue().strip())

    def test_delete_multiple_vnf_pm_job_exception(self):
        arg_list = [
            self.vnf_pm_jobs[0]['id'],
            'xxxx-yyyy-zzzz',
            self.vnf_pm_jobs[1]['id'],
        ]
        verify_list = [('vnf_pm_job_id', arg_list)]
        parsed_args = self.check_parser(self.delete_vnf_pm_job,
                                        arg_list, verify_list)

        self._mock_request_url_for_delete(0)

        url = os.path.join(self.url, 'vnfpm/v2/jobs',
                           'xxxx-yyyy-zzzz')
        self.requests_mock.register_uri(
            'GET', url, exc=exceptions.ConnectionFailed)

        self._mock_request_url_for_delete(1)
        exception = self.assertRaises(exceptions.CommandError,
                                      self.delete_vnf_pm_job.take_action,
                                      parsed_args)

        self.assertEqual('Failed to delete 1 of 3 VNF PM jobs.',
                         exception.message)
