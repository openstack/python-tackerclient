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
#
# @author: Isaku Yamahata, Intel

import sys

from tackerclient.tacker.v1_0.vm import device
from tackerclient.tests.unit import test_cli10


class CLITestV10VmDeviceJSON(test_cli10.CLITestV10Base):
    _RESOURCE = 'device'
    _RESOURCES = 'devices'

    def setUp(self):
        plurals = {'devices': 'device'}
        super(CLITestV10VmDeviceJSON, self).setUp(plurals=plurals)

    def test_create_device_all_params(self):
        cmd = device.CreateDevice(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        template_id = 'template_id'
        key = 'key'
        value = 'value'

        args = [
            '--device-template-id', template_id,
            '--%s' % key, value]
        position_names = ['template_id']
        position_values = [template_id]
        extra_body = {key: value}
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    def test_create_device_with_mandatory_params(self):
        cmd = device.CreateDevice(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        template_id = 'template_id'
        args = [
            '--device-template-id', template_id,
        ]
        position_names = ['template_id']
        position_values = [template_id]
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values)

    def test_list_devices(self):
        cmd = device.ListDevice(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_list_devices_pagenation(self):
        cmd = device.ListDevice(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_show_device_id(self):
        cmd = device.ShowDevice(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id, args,
                                 ['id'])

    def test_show_device_id_name(self):
        cmd = device.ShowDevice(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_device(self):
        cmd = device.UpdateDevice(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        key = 'new_key'
        value = 'new-value'
        self._test_update_resource(self._RESOURCE, cmd, my_id,
                                   [my_id, '--%s' % key, value],
                                   {key: value})

    def test_delete_device(self):
        cmd = device.DeleteDevice(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(self._RESOURCE, cmd, my_id, args)
