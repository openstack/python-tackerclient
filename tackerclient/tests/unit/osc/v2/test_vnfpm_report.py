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

import os

from oslo_utils.fixture import uuidsentinel
from unittest import mock

from tackerclient.common import exceptions
from tackerclient.osc.v2.vnfpm import vnfpm_report
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v2 import vnfpm_report_fakes


class TestVnfPmReport(base.FixturedTestCase):
    client_fixture_class = client.ClientFixture

    def setUp(self):
        super(TestVnfPmReport, self).setUp()
        self.url = client.TACKER_URL
        self.header = {'content-type': 'application/json'}
        self.app = mock.Mock()
        self.app_args = mock.Mock()
        self.client_manager = self.cs
        self.app.client_manager.tackerclient = self.client_manager


def _get_columns_vnfpm_report():
    columns = ['Entries']
    return columns


class TestShowVnfPmReport(TestVnfPmReport):

    def setUp(self):
        super(TestShowVnfPmReport, self).setUp()
        self.show_vnf_pm_reports = vnfpm_report.ShowVnfPmReport(
            self.app, self.app_args, cmd_name='vnfpm report show')

    def test_take_action(self):
        """Test of take_action()"""
        vnfpm_report_obj = vnfpm_report_fakes.vnf_pm_report_response()
        vnf_pm_job_id = uuidsentinel.vnf_pm_job_id
        vnf_pm_report_id = uuidsentinel.vnfpm_report_obj
        arg_list = [vnf_pm_job_id, vnf_pm_report_id]
        verify_list = [
            ('vnf_pm_job_id', vnf_pm_job_id),
            ('vnf_pm_report_id', vnf_pm_report_id)
        ]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_pm_reports, arg_list, verify_list)
        url = os.path.join(
            self.url, 'vnfpm/v2/pm_jobs', vnf_pm_job_id,
            'reports', vnf_pm_report_id)

        self.requests_mock.register_uri(
            'GET', url, headers=self.header, json=vnfpm_report_obj)

        columns, data = (self.show_vnf_pm_reports.take_action(parsed_args))

        self.assertCountEqual(_get_columns_vnfpm_report(), columns)

        _, attributes = vnfpm_report._get_columns(vnfpm_report_obj)
        expected_data = vnfpm_report_fakes.get_vnfpm_report_data(
            vnfpm_report_obj, columns=attributes)

        print(f'123, {expected_data}')
        print(f'456, {data}')
        self.assertListItemsEqual(expected_data, data)

    def test_take_action_vnf_pm_report_id_not_found(self):
        """Test if vnf-pm-report-id does not find."""
        vnf_pm_job_id = uuidsentinel.vnf_pm_job_id
        vnf_pm_report_id = uuidsentinel.vnf_pm_report_id
        arg_list = [vnf_pm_job_id, vnf_pm_report_id]
        verify_list = [
            ('vnf_pm_job_id', vnf_pm_job_id),
            ('vnf_pm_report_id', vnf_pm_report_id)
        ]

        # command param
        parsed_args = self.check_parser(
            self.show_vnf_pm_reports, arg_list, verify_list)

        url = os.path.join(
            self.url, 'vnfpm/v2/pm_jobs', vnf_pm_job_id,
            'reports', vnf_pm_report_id)
        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=404, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.show_vnf_pm_reports.take_action,
                          parsed_args)

    def test_take_action_internal_server_error(self):
        """Test for internal server error."""
        vnf_pm_job_id = uuidsentinel.vnf_pm_job_id
        vnf_pm_report_id = uuidsentinel.vnf_pm_report_id
        arg_list = [vnf_pm_job_id, vnf_pm_report_id]
        verify_list = [
            ('vnf_pm_job_id', vnf_pm_job_id),
            ('vnf_pm_report_id', vnf_pm_report_id)
        ]
        # command param
        parsed_args = self.check_parser(
            self.show_vnf_pm_reports, arg_list, verify_list)

        url = os.path.join(
            self.url, 'vnfpm/v2/pm_jobs', vnf_pm_job_id,
            'reports', vnf_pm_report_id)
        self.requests_mock.register_uri(
            'GET', url, headers=self.header, status_code=500, json={})

        self.assertRaises(exceptions.TackerClientException,
                          self.show_vnf_pm_reports.take_action,
                          parsed_args)
