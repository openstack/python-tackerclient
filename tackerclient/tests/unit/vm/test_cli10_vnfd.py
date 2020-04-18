# Copyright 2014 Intel Corporation
# All Rights Reserved.
#
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

import sys

from tackerclient.common.exceptions import InvalidInput
from tackerclient.tacker.v1_0.vnfm import vnfd
from tackerclient.tests.unit import test_cli10
from unittest.mock import mock_open
from unittest.mock import patch


class CLITestV10VmVNFDJSON(test_cli10.CLITestV10Base):
    _RESOURCE = 'vnfd'
    _RESOURCES = 'vnfds'

    def setUp(self):
        plurals = {'vnfds': 'vnfd'}
        super(CLITestV10VmVNFDJSON, self).setUp(plurals=plurals)

    @patch("tackerclient.tacker.v1_0.vnfm.vnfd.open",
           side_effect=mock_open(read_data="vnfd"),
           create=True)
    def test_create_vnfd_all_params(self, mo):
        cmd = vnfd.CreateVNFD(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'my-name'
        attr_key = 'vnfd'
        attr_val = 'vnfd'
        args = [
            name,
            '--vnfd-file', 'vnfd-file'
        ]
        position_names = ['name']
        position_values = [name]
        extra_body = {
            'service_types': [{'service_type': 'vnfd'}],
            'attributes': {attr_key: attr_val},
        }
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    @patch("tackerclient.tacker.v1_0.vnfm.vnfd.open",
           side_effect=mock_open(read_data="vnfd"),
           create=True)
    def test_create_vnfd_with_mandatory_params(self, mo):
        cmd = vnfd.CreateVNFD(
            test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        args = [name, '--vnfd-file', 'vnfd-file', ]
        position_names = ['name']
        position_values = [name]
        extra_body = {
            'service_types': [{'service_type': 'vnfd'}],
            'attributes': {'vnfd': 'vnfd'}
        }
        self._test_create_resource(self._RESOURCE, cmd, name, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    @patch("tackerclient.tacker.v1_0.vnfm.vnfd.open",
           side_effect=mock_open(read_data=""),
           create=True)
    def test_create_vnfd_with_empty_file(self, mo):
        cmd = vnfd.CreateVNFD(
            test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        args = [name, '--vnfd-file', 'vnfd-file', ]
        position_names = ['name']
        position_values = [name]
        extra_body = {
            'service_types': [{'service_type': 'vnfd'}],
            'attributes': {'vnfd': 'vnfd'}
        }
        err = None
        try:
            self._test_create_resource(self._RESOURCE, cmd, name, my_id,
                                       args, position_names, position_values,
                                       extra_body=extra_body)
        except InvalidInput:
            err = True
        self.assertEqual(True, err)

    def test_list_vnfds(self):
        cmd = vnfd.ListVNFD(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True,
                                  template_source='onboarded')

    def test_list_inline_vnfds(self):
        cmd = vnfd.ListVNFD(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True,
                                  template_source='inline')

    def test_list_all_vnfds(self):
        cmd = vnfd.ListVNFD(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True,
                                  template_source='all')

    def test_list_vnfds_pagenation(self):
        cmd = vnfd.ListVNFD(test_cli10.MyApp(sys.stdout), None)
        print(cmd)
        self._test_list_resources(self._RESOURCES, cmd, True,
                                  template_source='onboarded')

    def test_show_vnfd_id(self):
        cmd = vnfd.ShowVNFD(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id, args,
                                 ['id'])

    def test_show_vnfd_id_name(self):
        cmd = vnfd.ShowVNFD(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_delete_vnfd(self):
        cmd = vnfd.DeleteVNFD(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(self._RESOURCE, cmd, my_id, args)

    def test_multi_delete_vnfd(self):
        cmd = vnfd.DeleteVNFD(
            test_cli10.MyApp(sys.stdout), None)
        vnfd_ids = 'my-id1 my-id2 my-id3'
        args = [vnfd_ids]
        self._test_delete_resource(self._RESOURCE, cmd, vnfd_ids, args)
