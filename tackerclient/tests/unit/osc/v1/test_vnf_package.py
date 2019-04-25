# Copyright (C) 2019 NTT DATA
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
import mock

from tackerclient.common import exceptions
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.osc.v1.vnfpkgm import vnf_package
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v1 import vnf_package_fakes


def _get_columns_vnf_package(action='list', vnf_package_obj=None):
    columns = ['ID', 'Onboarding State', 'Operational State', 'Usage State',
               'User Defined Data', 'VNF Product Name']

    if action in ['show', 'create']:
        if vnf_package_obj and vnf_package_obj[
            'onboardingState'] == 'ONBOARDED':
            columns.extend(['Links', 'VNFD ID', 'VNF Provider',
                            'VNF Software Version', 'VNFD Version',
                            'Software Images'])
        else:
            columns.extend(['Links'])
            columns.remove('VNF Product Name')

    return columns


class TestVnfPackage(base.FixturedTestCase):
    client_fixture_class = client.ClientFixture

    def setUp(self):
        super(TestVnfPackage, self).setUp()
        self.url = client.TACKER_URL
        self.header = {'content-type': 'application/json'}
        self.app = mock.Mock()
        self.app_args = mock.Mock()
        self.client_manager = self.cs
        self.app.client_manager.tackerclient = self.client_manager


@ddt.ddt
class TestCreateVnfPackage(TestVnfPackage):

    def setUp(self):
        super(TestCreateVnfPackage, self).setUp()
        self.create_vnf_package = vnf_package.CreateVnfPackage(
            self.app, self.app_args, cmd_name='vnf package create')

    @ddt.data((["--user-data", 'Test_key=Test_value'],
               [('user_data', {'Test_key': 'Test_value'})]),
              ([], []))
    @ddt.unpack
    def test_take_action(self, arglist, verifylist):
        # command param
        parsed_args = self.check_parser(self.create_vnf_package, arglist,
                                        verifylist)

        if arglist:
            json = vnf_package_fakes.vnf_package_obj(
                attrs={'userDefinedData': {'Test_key': 'Test_value'}})
        else:
            json = vnf_package_fakes.vnf_package_obj()
        self.requests_mock.register_uri(
            'POST', self.url + '/vnfpkgm/v1/vnf_packages',
            json=json, headers=self.header)

        columns, data = (self.create_vnf_package.take_action(parsed_args))
        self.assertItemsEqual(_get_columns_vnf_package(action='create'),
                              columns)
        self.assertItemsEqual(vnf_package_fakes.get_vnf_package_data(json),
                              data)


class TestListVnfPackage(TestVnfPackage):

    _vnf_packages = vnf_package_fakes.create_vnf_packages(count=3)

    def setUp(self):
        super(TestListVnfPackage, self).setUp()
        self.list_vnf_package = vnf_package.ListVnfPackage(
            self.app, self.app_args, cmd_name='vnf package list')

    def test_take_action(self):
        parsed_args = self.check_parser(self.list_vnf_package, [], [])
        self.requests_mock.register_uri(
            'GET', self.url + '/vnfpkgm/v1/vnf_packages',
            json=self._vnf_packages, headers=self.header)
        actual_columns, data = self.list_vnf_package.take_action(parsed_args)

        expected_data = []
        headers, columns = tacker_osc_utils.get_column_definitions(
            vnf_package._attr_map, long_listing=True)

        for vnf_package_obj in self._vnf_packages['vnf_packages']:
            expected_data.append(vnf_package_fakes.get_vnf_package_data(
                vnf_package_obj, columns=columns, list_action=True))

        self.assertItemsEqual(_get_columns_vnf_package(), actual_columns)
        self.assertItemsEqual(expected_data, list(data))


@ddt.ddt
class TestShowVnfPackage(TestVnfPackage):

    def setUp(self):
        super(TestShowVnfPackage, self).setUp()
        self.show_vnf_package = vnf_package.ShowVnfPackage(
            self.app, self.app_args, cmd_name='vnf package show')

    @ddt.data(True, False)
    def test_take_action(self, onboarded):
        vnf_package_obj = vnf_package_fakes.vnf_package_obj(
            onboarded_state=onboarded)
        arglist = [vnf_package_obj['id']]
        verifylist = [('vnf_package', vnf_package_obj['id'])]
        parsed_args = self.check_parser(self.show_vnf_package, arglist,
                                        verifylist)
        url = self.url + '/vnfpkgm/v1/vnf_packages/' + vnf_package_obj['id']
        self.requests_mock.register_uri('GET', url, json=vnf_package_obj,
                                        headers=self.header)
        columns, data = (self.show_vnf_package.take_action(parsed_args))
        self.assertItemsEqual(_get_columns_vnf_package(
            vnf_package_obj=vnf_package_obj, action='show'), columns)
        self.assertItemsEqual(
            vnf_package_fakes.get_vnf_package_data(vnf_package_obj), data)

    def test_show_no_options(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.show_vnf_package, [], [])


class TestDeleteVnfPackage(TestVnfPackage):

    def setUp(self):
        super(TestDeleteVnfPackage, self).setUp()
        self.delete_vnf_package = vnf_package.DeleteVnfPackage(
            self.app, self.app_args, cmd_name='vnf package delete')

        # The Vnf Package to delete
        self._vnf_package = vnf_package_fakes.create_vnf_packages(count=3)

    def _mock_request_url_for_delete(self, vnf_pkg_index):
            url = (self.url + '/vnfpkgm/v1/vnf_packages/' +
                   self._vnf_package['vnf_packages'][vnf_pkg_index]['id'])

            json = self._vnf_package['vnf_packages'][vnf_pkg_index]

            self.requests_mock.register_uri('GET', url, json=json,
                                            headers=self.header)
            self.requests_mock.register_uri('DELETE', url,
                                            headers=self.header, json={})

    def test_delete_one_vnf_package(self):
        arglist = [self._vnf_package['vnf_packages'][0]['id']]
        verifylist = [('vnf-package', [self._vnf_package['vnf_packages']
                                       [0]['id']])]

        parsed_args = self.check_parser(self.delete_vnf_package, arglist,
                                        verifylist)

        self._mock_request_url_for_delete(0)
        result = self.delete_vnf_package.take_action(parsed_args)
        self.assertIsNone(result)

    def test_delete_multiple_vnf_package(self):
        arglist = []
        for vnf_pkg in self._vnf_package['vnf_packages']:
            arglist.append(vnf_pkg['id'])
        verifylist = [('vnf-package', arglist)]
        parsed_args = self.check_parser(self.delete_vnf_package, arglist,
                                        verifylist)
        for i in range(0, 3):
            self._mock_request_url_for_delete(i)

        result = self.delete_vnf_package.take_action(parsed_args)
        self.assertIsNone(result)

    def test_delete_multiple_vnf_package_exception(self):
        arglist = [
            self._vnf_package['vnf_packages'][0]['id'],
            'xxxx-yyyy-zzzz',
            self._vnf_package['vnf_packages'][1]['id'],
        ]
        verifylist = [
            ('vnf-package', arglist),
        ]
        parsed_args = self.check_parser(self.delete_vnf_package,
                                        arglist, verifylist)

        self._mock_request_url_for_delete(0)

        url = (self.url + '/vnfpkgm/v1/vnf_packages/' + 'xxxx-yyyy-zzzz')
        body = {"error": exceptions.NotFound('404')}
        self.requests_mock.register_uri('GET', url, body=body,
                                        status_code=404, headers=self.header)
        self._mock_request_url_for_delete(1)
        self.assertRaises(exceptions.CommandError,
                          self.delete_vnf_package.take_action,
                          parsed_args)
