# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2014 Intel
# Copyright 2014 Isaku Yamahata <isaku.yamahata at intel com>
#                               <isaku.yamahata at gmail com>
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

from tackerclient.tacker.v1_0.vm import vnfd
from tackerclient.tests.unit import test_cli10


class CLITestV10VmVNFDJSON(test_cli10.CLITestV10Base):
    _RESOURCE = 'vnfd'
    _RESOURCES = 'vnfds'

    def setUp(self):
        plurals = {'vnfds': 'vnfd'}
        super(CLITestV10VmVNFDJSON, self).setUp(plurals=plurals)

    def test_create_vnfd_all_params(self):
        cmd = vnfd.CreateVNFD(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'my-name'
        mgmt_driver = 'noop'
        infra_driver = 'heat'
        attr_key = 'vnfd'
        attr_val = 'vnfd'
        args = [
            '--name', name,
            '--vnfd', 'vnfd'
        ]
        position_names = ['name', 'mgmt_driver', 'infra_driver']
        position_values = [name, mgmt_driver, infra_driver]
        extra_body = {
            'service_types': [{'service_type': 'vnfd'}],
            'attributes': {attr_key: attr_val},
        }
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    def test_create_vnfd_with_mandatory_params(self):
        cmd = vnfd.CreateVNFD(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        mgmt_driver = 'noop'
        infra_driver = 'heat'
        args = ['--vnfd', 'vnfd', ]
        position_names = ['mgmt_driver', 'infra_driver']
        position_values = [mgmt_driver, infra_driver]
        extra_body = {
            'service_types': [{'service_type': 'vnfd'}],
            'attributes': {'vnfd': 'vnfd'}
        }
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    def test_list_vnfds(self):
        cmd = vnfd.ListVNFD(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_list_vnfds_pagenation(self):
        cmd = vnfd.ListVNFD(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

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
