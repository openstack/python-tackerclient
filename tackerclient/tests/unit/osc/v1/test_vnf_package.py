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

import copy
import filecmp
import os
import shutil
import sys
import tempfile
from unittest import mock

import ddt
import zipfile

from tackerclient import client as root_client
from tackerclient.common import exceptions
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.osc.v1.vnfpkgm import vnf_package
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client
from tackerclient.tests.unit.osc.v1 import vnf_package_fakes
from tackerclient.tests.unit.test_cli10 import MyResp
from tackerclient.v1_0 import client as proxy_client


def _create_zip():
    vnf_package_path = ('./tackerclient/tests//unit/osc/v1/fixture_data/'
                        'sample_vnf_package')
    tmpdir = tempfile.mkdtemp()
    tmparchive = os.path.join(tmpdir, 'sample_vnf_package')
    zip_file = shutil.make_archive(tmparchive, 'zip', vnf_package_path)
    return zip_file, tmpdir


def _get_columns_vnf_package(action='list', vnf_package_obj=None):
    columns = []
    if action == 'update':
        if vnf_package_obj.get('userDefinedData'):
            columns.extend(['User Defined Data'])
        if vnf_package_obj.get('operationalState'):
            columns.extend(['Operational State'])
        return columns

    columns.extend(['ID', 'Onboarding State', 'Operational State',
                    'Usage State', 'User Defined Data', 'Links'])

    if action in ['show', 'create']:
        if vnf_package_obj and vnf_package_obj[
            'onboardingState'] == 'ONBOARDED':
            columns.extend(['VNFD ID',
                            'VNF Provider',
                            'VNF Software Version',
                            'VNFD Version',
                            'Software Images',
                            'VNF Product Name',
                            'Checksum',
                            'Additional Artifacts'])

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
        self.assertCountEqual(_get_columns_vnf_package(), columns)
        headers, attributes = vnf_package._get_columns(json)
        self.assertListItemsEqual(vnf_package_fakes.get_vnf_package_data(
            json, columns=attributes), data)


@ddt.ddt
class TestListVnfPackage(TestVnfPackage):

    def setUp(self):
        super(TestListVnfPackage, self).setUp()
        self.list_vnf_package = vnf_package.ListVnfPackage(
            self.app, self.app_args, cmd_name='vnf package list')
        self._vnf_packages = self._get_vnf_packages()

    def _get_vnf_packages(self, onboarded_vnf_package=False):
        return vnf_package_fakes.create_vnf_packages(
            count=3, onboarded_vnf_package=onboarded_vnf_package)

    def get_list_columns(self, all_fields=False, exclude_fields=None,
                         extra_fields=None, exclude_default=False):

        columns = ['Id', 'Vnf Product Name', 'Onboarding State', 'Usage State',
                   'Operational State', 'Links']
        complex_columns = [
            'Checksum',
            'Software Images',
            'User Defined Data',
            'Additional Artifacts']
        simple_columns = ['Vnfd Version', 'Vnf Provider', 'Vnfd Id',
                          'Vnf Software Version']

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

    def _get_mock_response_for_list_vnf_packages(
            self, filter_attribute, json=None):
        self.requests_mock.register_uri(
            'GET', self.url + '/vnfpkgm/v1/vnf_packages?' + filter_attribute,
            json=json if json else self._get_vnf_packages(),
            headers=self.header)

    def test_take_action_default_fields(self):
        parsed_args = self.check_parser(self.list_vnf_package, [], [])
        self.requests_mock.register_uri(
            'GET', self.url + '/vnfpkgm/v1/vnf_packages',
            json=self._vnf_packages, headers=self.header)
        actual_columns, data = self.list_vnf_package.take_action(parsed_args)
        expected_data = []
        headers, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnf_package.get_attributes(), long_listing=True)

        for vnf_package_obj in self._vnf_packages['vnf_packages']:
            expected_data.append(vnf_package_fakes.get_vnf_package_data(
                vnf_package_obj, columns=columns, list_action=True))
        self.assertCountEqual(self.get_list_columns(), actual_columns)
        self.assertListItemsEqual(expected_data, list(data))

    @ddt.data('all_fields', 'exclude_default')
    def test_take_action(self, arg):
        parsed_args = self.check_parser(
            self.list_vnf_package,
            ["--" + arg, "--filter", '(eq,onboardingState,ONBOARDED)'],
            [(arg, True), ('filter', '(eq,onboardingState,ONBOARDED)')])
        vnf_packages = self._get_vnf_packages(onboarded_vnf_package=True)
        self._get_mock_response_for_list_vnf_packages(
            'filter=(eq,onboardingState,ONBOARDED)&' + arg, json=vnf_packages)

        actual_columns, data = self.list_vnf_package.take_action(parsed_args)
        expected_data = []
        kwargs = {arg: True}
        headers, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnf_package.get_attributes(**kwargs), long_listing=True)

        for vnf_package_obj in vnf_packages['vnf_packages']:
            expected_data.append(vnf_package_fakes.get_vnf_package_data(
                vnf_package_obj, columns=columns, list_action=True, **kwargs))

        self.assertCountEqual(self.get_list_columns(**kwargs), actual_columns)
        self.assertListItemsEqual(expected_data, list(data))

    def test_take_action_with_pagination(self):
        next_links_num = 3
        parsed_args = self.check_parser(self.list_vnf_package, [], [])

        path = os.path.join(self.url, '/vnfpkgm/v1/vnf_packages?')

        links = [0] * next_links_num
        link_headers = [0] * next_links_num

        for i in range(next_links_num):
            links[i] = (
                '{base_url}?nextpage_opaque_marker={vnf_package_id}'.format(
                    base_url=path,
                    vnf_package_id=self._vnf_packages
                    ['vnf_packages'][i]['id']))
            link_headers[i] = copy.deepcopy(self.header)
            link_headers[i]['Link'] = '<{link_url}>; rel="next"'.format(
                link_url=links[i])

        self.requests_mock.register_uri(
            'GET', path, json=[self._vnf_packages['vnf_packages'][0]],
            headers=link_headers[0])
        self.requests_mock.register_uri(
            'GET', links[0], json=[self._vnf_packages['vnf_packages'][1]],
            headers=link_headers[1])
        self.requests_mock.register_uri(
            'GET', links[1], json=[self._vnf_packages['vnf_packages'][2]],
            headers=link_headers[2])
        self.requests_mock.register_uri(
            'GET', links[2], json=[], headers=self.header)

        actual_columns, data = self.list_vnf_package.take_action(parsed_args)

        kwargs = {}
        headers, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnf_package.get_attributes(**kwargs), long_listing=True)

        expected_data = []
        for vnf_package_obj in self._vnf_packages['vnf_packages']:
            expected_data.append(vnf_package_fakes.get_vnf_package_data(
                vnf_package_obj, columns=columns, list_action=True, **kwargs))

        self.assertCountEqual(self.get_list_columns(**kwargs), actual_columns)
        self.assertListItemsEqual(expected_data, list(data))

    def test_take_action_with_exclude_fields(self):
        parsed_args = self.check_parser(
            self.list_vnf_package,
            ["--exclude_fields", 'softwareImages,checksum,'
                                 'userDefinedData,additionalArtifacts',
             "--filter", '(eq,onboardingState,ONBOARDED)'],
            [('exclude_fields', 'softwareImages,checksum,'
                                'userDefinedData,additionalArtifacts'),
             ('filter', '(eq,onboardingState,ONBOARDED)')])
        vnf_packages = self._get_vnf_packages(onboarded_vnf_package=True)
        updated_vnf_packages = {'vnf_packages': []}
        for vnf_pkg in vnf_packages['vnf_packages']:
            vnf_pkg.pop('softwareImages')
            vnf_pkg.pop('checksum')
            vnf_pkg.pop('userDefinedData')
            vnf_pkg.pop('additionalArtifacts')
            updated_vnf_packages['vnf_packages'].append(vnf_pkg)
        self._get_mock_response_for_list_vnf_packages(
            'filter=(eq,onboardingState,ONBOARDED)&'
            'exclude_fields=softwareImages,checksum,'
            'userDefinedData,additionalArtifacts',
            json=updated_vnf_packages)

        actual_columns, data = self.list_vnf_package.take_action(parsed_args)
        expected_data = []
        headers, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnf_package.get_attributes(
                exclude_fields=['softwareImages', 'checksum',
                                'userDefinedData', 'additionalArtifacts']),
            long_listing=True)

        for vnf_package_obj in updated_vnf_packages['vnf_packages']:
            expected_data.append(vnf_package_fakes.get_vnf_package_data(
                vnf_package_obj, columns=columns, list_action=True))
        expected_columns = self.get_list_columns(
            exclude_fields=['Software Images', 'Checksum',
                            'User Defined Data', 'Additional Artifacts'])
        self.assertCountEqual(expected_columns, actual_columns)
        self.assertListItemsEqual(expected_data, list(data))

    @ddt.data((['--all_fields', '--fields', 'softwareImages'],
               [('all_fields', True), ('fields', 'softwareImages')]),
              (['--all_fields', '--exclude_fields', 'checksum'],
               [('all_fields', True), ('exclude_fields', 'checksum')]),
              (['--fields', 'softwareImages', '--exclude_fields', 'checksum'],
               [('fields', 'softwareImages'), ('exclude_fields', 'checksum')]))
    @ddt.unpack
    def test_take_action_with_invalid_combination(self, arglist, verifylist):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.list_vnf_package, arglist, verifylist)

    def test_take_action_with_valid_combination(self):
        parsed_args = self.check_parser(
            self.list_vnf_package,
            ["--fields", 'softwareImages,checksum', "--exclude_default"],
            [('fields', 'softwareImages,checksum'), ('exclude_default', True)])
        vnf_packages = self._get_vnf_packages(onboarded_vnf_package=True)
        updated_vnf_packages = {'vnf_packages': []}
        for vnf_pkg in vnf_packages['vnf_packages']:
            vnf_pkg.pop('userDefinedData')
            updated_vnf_packages['vnf_packages'].append(vnf_pkg)

        self._get_mock_response_for_list_vnf_packages(
            'exclude_default&fields=softwareImages,checksum',
            json=updated_vnf_packages)

        actual_columns, data = self.list_vnf_package.take_action(parsed_args)
        expected_data = []
        headers, columns = tacker_osc_utils.get_column_definitions(
            self.list_vnf_package.get_attributes(
                extra_fields=['softwareImages', 'checksum'],
                exclude_default=True),
            long_listing=True)

        for vnf_package_obj in updated_vnf_packages['vnf_packages']:
            expected_data.append(vnf_package_fakes.get_vnf_package_data(
                vnf_package_obj, columns=columns, list_action=True,
                exclude_default=True))

        self.assertCountEqual(self.get_list_columns(
            extra_fields=['Software Images', 'Checksum'],
            exclude_default=True),
            actual_columns)
        self.assertListItemsEqual(expected_data, list(data))


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
        self.assertCountEqual(_get_columns_vnf_package(
            vnf_package_obj=vnf_package_obj, action='show'), columns)

        headers, attributes = vnf_package._get_columns(vnf_package_obj)
        self.assertListItemsEqual(
            vnf_package_fakes.get_vnf_package_data(vnf_package_obj,
                                                   columns=attributes), data)

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


@ddt.ddt
class TestUploadVnfPackage(TestVnfPackage):

    # The new vnf package created.
    _vnf_package = vnf_package_fakes.vnf_package_obj(
        attrs={'userDefinedData': {'Test_key': 'Test_value'}})

    def setUp(self):
        super(TestUploadVnfPackage, self).setUp()
        self.upload_vnf_package = vnf_package.UploadVnfPackage(
            self.app, self.app_args, cmd_name='vnf package upload')

    def test_upload_no_options(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.upload_vnf_package, [], [])

    def _mock_request_url_for_upload(self, method, status_code=202, body={}):
        if method == 'PUT':
            self.header = {'content-type': 'application/zip'}
            url = (self.url + '/vnfpkgm/v1/vnf_packages/' +
                   self._vnf_package['id'] + '/package_content')
        else:
            url = (self.url + '/vnfpkgm/v1/vnf_packages/' +
                   self._vnf_package['id'] + '/package_content/'
                                             'upload_from_uri')

        self.requests_mock.register_uri(method, url, json=body,
                                        headers=self.header,
                                        status_code=status_code)

    def _get_arglist_and_verifylist(self, method, path):
        if method == 'path':
            arglist = [
                self._vnf_package['id'],
                "--path", path
            ]
            verifylist = [
                ('path', path),
                ('vnf_package', self._vnf_package['id'])
            ]
        else:
            arglist = [
                self._vnf_package['id'],
                "--url", "http://uri:8000/test.zip",
                "--user-name", "Test_username",
                "--password", "Test_passoword",
            ]
            verifylist = [
                ('url', "http://uri:8000/test.zip"),
                ('user_name', 'Test_username'),
                ('password', 'Test_passoword'),
                ('vnf_package', self._vnf_package['id'])
            ]
        return arglist, verifylist

    @ddt.data('path', 'url')
    def test_upload_vnf_package(self, method):
        path = None
        if method == 'path':
            zip_file, temp_dir = _create_zip()
            path = zip_file

        arglist, verifylist = self._get_arglist_and_verifylist(method,
                                                               path)
        parsed_args = self.check_parser(self.upload_vnf_package, arglist,
                                        verifylist)
        with mock.patch.object(proxy_client.ClientBase,
                               '_handle_fault_response') as m:
            if method == 'url':
                self._mock_request_url_for_upload('POST')
                self.upload_vnf_package.take_action(parsed_args)
            else:
                self._mock_request_url_for_upload('PUT')
                self.upload_vnf_package.take_action(parsed_args)
                # Delete temporary folder
                shutil.rmtree(temp_dir)
        # check no fault response is received
        self.assertNotCalled(m)

    @ddt.data('path')
    @mock.patch.object(proxy_client.ClientBase, 'deserialize')
    def test_upload_vnf_package_check_content_type(self, method, mock_des):
        path = None
        if method == 'path':
            zip_file, temp_dir = _create_zip()
            path = zip_file

        arglist, verifylist = self._get_arglist_and_verifylist(method, path)
        parsed_args = self.check_parser(self.upload_vnf_package, arglist,
                                        verifylist)
        mock_des.return_value = {}
        with mock.patch.object(root_client.HTTPClient,
                               'do_request') as mock_req:
            headers = {'Content-Type': 'application/json'}
            mock_req.return_value = (MyResp(202, headers=headers), None)
            self._mock_request_url_for_upload('PUT')
            self.upload_vnf_package.take_action(parsed_args)
            # Delete temporary folder
            shutil.rmtree(temp_dir)
            mock_req.assert_called_once_with(
                f'/vnfpkgm/v1/vnf_packages/{self._vnf_package["id"]}'
                '/package_content', 'PUT',
                body=mock.ANY, headers=mock.ANY,
                content_type='application/zip', accept='json')

    def test_upload_vnf_package_with_conflict_error(self):
        # Scenario in which vnf package is already in on-boarded state
        zip_file, temp_dir = _create_zip()
        arglist, verifylist = self._get_arglist_and_verifylist('path',
                                                               zip_file)

        parsed_args = self.check_parser(self.upload_vnf_package, arglist,
                                        verifylist)

        body = {"conflictingRequest": {
            "message": "VNF Package " + self._vnf_package['id'] +
                       " onboarding state is not CREATED", "code": 409}}
        self._mock_request_url_for_upload('PUT', status_code=409, body=body)

        self.assertRaises(exceptions.TackerClientException,
                          self.upload_vnf_package.take_action, parsed_args)
        # Delete temporary folder
        shutil.rmtree(temp_dir)

    def test_upload_vnf_package_failed_with_404_not_found(self):
        # Scenario in which vnf package is not found
        zip_file, temp_dir = _create_zip()
        arglist = [
            'dumy-id',
            "--path", zip_file
        ]
        verifylist = [
            ('path', zip_file),
            ('vnf_package', 'dumy-id')
        ]

        parsed_args = self.check_parser(self.upload_vnf_package, arglist,
                                        verifylist)

        error_message = "Can not find requested vnf package: dummy-id"
        body = {"itemNotFound": {"message": error_message, "code": 404}}
        url = self.url + '/vnfpkgm/v1/vnf_packages/dumy-id/package_content'

        self.requests_mock.register_uri(
            'PUT', url, json=body,
            status_code=404)

        exception = self.assertRaises(
            exceptions.TackerClientException,
            self.upload_vnf_package.take_action, parsed_args)

        self.assertEqual(error_message, exception.message)
        # Delete temporary folder
        shutil.rmtree(temp_dir)


@ddt.ddt
class TestUpdateVnfPackage(TestVnfPackage):

    def setUp(self):
        super(TestUpdateVnfPackage, self).setUp()
        self.update_vnf_package = vnf_package.UpdateVnfPackage(
            self.app, self.app_args, cmd_name='vnf package update')

    @ddt.data((["--user-data", 'Test_key=Test_value',
                "--operational-state", 'DISABLED'],
               [('user_data', {'Test_key': 'Test_value'}),
                ('operational_state', 'DISABLED')]),
              (["--user-data", 'Test_key=Test_value'],
               [('user_data', {'Test_key': 'Test_value'})]),
              (["--operational-state", 'DISABLED'],
               [('operational_state', 'DISABLED')]))
    @ddt.unpack
    def test_take_action(self, arglist, verifylist):
        vnf_package_obj = vnf_package_fakes.vnf_package_obj(
            onboarded_state=True)
        arglist.append(vnf_package_obj['id'])
        verifylist.append(('vnf_package', vnf_package_obj['id']))

        parsed_args = self.check_parser(self.update_vnf_package, arglist,
                                        verifylist)
        url = os.path.join(self.url, 'vnfpkgm/v1/vnf_packages',
                           vnf_package_obj['id'])
        fake_response = vnf_package_fakes.get_fake_update_vnf_package_obj(
            arglist)
        self.requests_mock.register_uri('PATCH', url,
                                        json=fake_response,
                                        headers=self.header)

        columns, data = self.update_vnf_package.take_action(parsed_args)
        self.assertCountEqual(_get_columns_vnf_package(
            vnf_package_obj=fake_response, action='update'), columns)
        self.assertListItemsEqual(
            vnf_package_fakes.get_vnf_package_data(fake_response), data)

    @ddt.data((["--user-data", 'Test_key=Test_value'],
               [('user_data', {'Test_key': 'Test_value'})]))
    @ddt.unpack
    @mock.patch.object(proxy_client.ClientBase, 'deserialize')
    def test_take_action_check_content_type(
            self, arglist, verifylist, mock_des):
        vnf_package_obj = vnf_package_fakes.vnf_package_obj(
            onboarded_state=True)
        arglist.append(vnf_package_obj['id'])
        verifylist.append(('vnf_package', vnf_package_obj['id']))
        mock_des.return_value = {}

        parsed_args = self.check_parser(self.update_vnf_package, arglist,
                                        verifylist)
        url = os.path.join(self.url, 'vnfpkgm/v1/vnf_packages',
                           vnf_package_obj['id'])
        fake_response = vnf_package_fakes.get_fake_update_vnf_package_obj(
            arglist)
        self.requests_mock.register_uri('PATCH', url, json=fake_response,
                                        headers=self.header)

        with mock.patch.object(root_client.HTTPClient,
                               'do_request') as mock_req:
            headers = {'Content-Type': 'application/json'}
            mock_req.return_value = (MyResp(200, headers=headers), None)
            self.update_vnf_package.take_action(parsed_args)
            mock_req.assert_called_once_with(
                f'/vnfpkgm/v1/vnf_packages/{vnf_package_obj["id"]}', 'PATCH',
                body=mock.ANY, headers=mock.ANY,
                content_type='application/merge-patch+json', accept='json')

    def test_update_no_options(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.update_vnf_package, [], [])

    def test_update_without_user_data_and_operational_state(self):
        vnf_package_obj = vnf_package_fakes.vnf_package_obj(
            onboarded_state=True)
        arglist = [vnf_package_obj['id']]

        verifylist = [('vnf_package', vnf_package_obj['id'])]

        parsed_args = self.check_parser(self.update_vnf_package, arglist,
                                        verifylist)
        self.assertRaises(SystemExit, self.update_vnf_package.take_action,
                          parsed_args)


@ddt.ddt
class TestDownloadVnfPackage(TestVnfPackage):

    # The new vnf package created.
    _vnf_package = vnf_package_fakes.vnf_package_obj(
        attrs={'userDefinedData': {'Test_key': 'Test_value'}})

    def setUp(self):
        super(TestDownloadVnfPackage, self).setUp()
        self.download_vnf_package = vnf_package.DownloadVnfPackage(
            self.app, self.app_args, cmd_name='vnf package download')

    def test_download_no_options(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.download_vnf_package, [], [])

    def _mock_request_url_for_download_vnfd(self, content_type, vnfd_data):
        self.header = {'content-type': content_type}
        url = os.path.join(self.url, 'vnfpkgm/v1/vnf_packages',
                           self._vnf_package['id'], 'vnfd')

        if content_type == 'text/plain':
            self.requests_mock.register_uri('GET', url,
                                            headers=self.header,
                                            text=vnfd_data)
        else:
            self.requests_mock.register_uri('GET', url,
                                            headers=self.header,
                                            content=vnfd_data)

    def _get_arglist_and_verifylist(self, accept_type, file_name):
        arglist = [
            self._vnf_package['id'],
            '--vnfd',
            '--type', accept_type,
            '--file', file_name
        ]
        verifylist = [
            ('type', accept_type),
            ('vnfd', True),
            ('vnf_package', self._vnf_package['id']),
            ('file', file_name)
        ]
        return arglist, verifylist

    def test_download_vnfd_from_vnf_package_for_type_text_plain(self):
        test_file = ('./tackerclient/tests//unit/osc/v1/fixture_data/'
                     'sample_vnf_package/Definitions/'
                     'etsi_nfv_sol001_common_types.yaml')

        local_file = tempfile.NamedTemporaryFile(suffix='vnfd_data.yaml')
        vnfd_data = open(test_file, 'r').read()
        arglist, verifylist = self._get_arglist_and_verifylist(
            'text/plain', local_file.name)
        parsed_args = self.check_parser(self.download_vnf_package, arglist,
                                        verifylist)
        self._mock_request_url_for_download_vnfd('text/plain', vnfd_data)
        self.download_vnf_package.take_action(parsed_args)
        self.assertTrue(filecmp.cmp(test_file, local_file.name),
                        "Downloaded contents don't match test file")

    @ddt.data('application/zip', 'both')
    def test_download_vnfd_from_vnf_package(self, accept_type):
        test_file, temp_dir = _create_zip()
        # File in which VNFD data will be stored.
        # For testing purpose we are creating temporary zip file.
        local_file = tempfile.NamedTemporaryFile(suffix='vnfd_data.zip')
        vnfd_data = open(test_file, 'rb').read()
        arglist, verifylist = self._get_arglist_and_verifylist(
            accept_type, local_file.name)
        parsed_args = self.check_parser(self.download_vnf_package, arglist,
                                        verifylist)
        # When --type argument is set to 'both', then 'Accept' header in
        # request is set to 'text/plain,application/zip' now it is up to the
        # NFVO to choose the format to return for a single-file VNFD and for
        # a multi-file VNFD, a ZIP file shall be returned. Here we have taken
        # the example of multi-file vnfd hence its retuning zip file and
        # setting the 'Content-Type' as 'application/zip' in response header.
        self._mock_request_url_for_download_vnfd('application/zip', vnfd_data)
        self.download_vnf_package.take_action(parsed_args)
        self.assertTrue(filecmp.cmp(test_file, local_file.name),
                        "Downloaded contents don't match test file")
        self.assertTrue(self._check_valid_zip_file(local_file.name))
        shutil.rmtree(temp_dir)

    def _check_valid_zip_file(self, zip_file):
        with zipfile.ZipFile(zip_file) as zf:
            ret = zf.testzip()
        return False if ret else True

    @mock.patch('builtins.print')
    def test_download_vnfd_from_vnf_package_without_file_arg(self, mock_print):
        # --file argument is optional when --type is set to 'text/plain'.
        arglist = [
            self._vnf_package['id'],
            '--vnfd',
            '--type', 'text/plain',
        ]
        verifylist = [
            ('type', 'text/plain'),
            ('vnfd', True),
            ('vnf_package', self._vnf_package['id']),
        ]
        parsed_args = self.check_parser(self.download_vnf_package, arglist,
                                        verifylist)
        test_file = ('./tackerclient/tests//unit/osc/v1/fixture_data/'
                     'sample_vnf_package/Definitions/'
                     'etsi_nfv_sol001_common_types.yaml')

        vnfd_data = open(test_file, 'r').read()
        self._mock_request_url_for_download_vnfd('text/plain', vnfd_data)
        self.download_vnf_package.take_action(parsed_args)
        mock_print.assert_called_once_with(vnfd_data)

    @ddt.data('application/zip', 'both')
    def test_download_vnfd_from_vnf_package_failed_with_no_file_arg(
            self, accept_type):
        arglist = [
            self._vnf_package['id'],
            '--vnfd',
            '--type', accept_type,
        ]
        verifylist = [
            ('type', accept_type),
            ('vnfd', True),
            ('vnf_package', self._vnf_package['id']),
        ]
        parsed_args = self.check_parser(self.download_vnf_package, arglist,
                                        verifylist)
        with mock.patch.object(sys.stdout, "isatty") as mock_isatty:
            mock_isatty.return_value = True
            self.assertRaises(SystemExit,
                              self.download_vnf_package.take_action,
                              parsed_args)

    def test_download_vnf_package(self):
        file_name = 'vnf_package_data.zip'
        test_file, temp_dir = _create_zip()

        # file in which VNF Package data will be stored.
        # for testing purpose we are creating temporary zip file.
        local_file = tempfile.NamedTemporaryFile(suffix=file_name)
        vnf_package_data = open(test_file, 'rb').read()

        arglist = [
            self._vnf_package['id'],
            '--file', local_file.name
        ]
        verifylist = [
            ('vnf_package', self._vnf_package['id']),
            ('file', local_file.name)
        ]

        parsed_args = self.check_parser(self.download_vnf_package, arglist,
                                        verifylist)

        url = os.path.join(self.url, '/vnfpkgm/v1/vnf_packages',
                           self._vnf_package['id'], 'package_content')

        self.requests_mock.register_uri(
            'GET', url, headers={'content-type': 'application/zip'},
            content=vnf_package_data)

        self.download_vnf_package.take_action(parsed_args)
        self.assertTrue(filecmp.cmp(test_file, local_file.name),
                        "Downloaded contents don't match test file")
        self.assertTrue(self._check_valid_zip_file(local_file.name))
        shutil.rmtree(temp_dir)


@ddt.ddt
class TestDownloadVnfPackageArtifact(TestVnfPackage):
    # The new vnf package created.
    _vnf_package = vnf_package_fakes.vnf_package_obj(
        attrs={'userDefinedData': {'Test_key': 'Test_value'}})

    def setUp(self):
        super(TestDownloadVnfPackageArtifact, self).setUp()
        self.download_vnf_package_artifacts = vnf_package.\
            DownloadVnfPackageArtifact(
                self.app, self.app_args,
                cmd_name='vnf package artifact download')

    def test_download_no_options(self):
        self.assertRaises(base.ParserException, self.check_parser,
                          self.download_vnf_package_artifacts, [], [])

    def _mock_request_url_for_download_artifacts(
        self, artifact_path, artifact_data):
        self.header = {'content-type': 'text/plain'}
        url = os.path.join(self.url, 'vnfpkgm/v1/vnf_packages',
                           self._vnf_package['id'], 'artifacts', artifact_path)
        self.requests_mock.register_uri('GET', url,
                                        headers=self.header,
                                        text=artifact_data)

    def _get_arglist_and_verifylist(self, localfile):
        arglist = [
            self._vnf_package['id'],
            localfile.name[1:],
            '--file', localfile.name
        ]
        verifylist = [
            ('vnf_package', self._vnf_package['id']),
            ('artifact_path', localfile.name[1:]),
            ('file', localfile.name)
        ]
        return arglist, verifylist

    def test_download_artifacts_from_vnf_package(self):
        test_file = ('./tackerclient/tests//unit/osc/v1/fixture_data/'
                     'sample_vnf_package_artifacts/Scripts/'
                     'install.sh')

        local_file = tempfile.NamedTemporaryFile(suffix='install.sh')
        artifact_data = open(test_file, 'r').read()
        arglist, verifylist = self._get_arglist_and_verifylist(
            local_file)
        parsed_args = self.check_parser(
            self.download_vnf_package_artifacts, arglist, verifylist)
        self._mock_request_url_for_download_artifacts(
            local_file.name[1:], artifact_data)
        self.download_vnf_package_artifacts.take_action(parsed_args)
        self.assertTrue(filecmp.cmp(test_file, local_file.name),
                        "Downloaded contents don't match test file")
