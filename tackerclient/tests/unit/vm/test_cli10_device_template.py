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

from tackerclient.tacker.v1_0.vm import device_template
from tackerclient.tests.unit import test_cli10


class CLITestV10VmDeviceTemplateJSON(test_cli10.CLITestV10Base):
    _RESOURCE = 'device_template'
    _RESOURCES = 'device_templates'

    def setUp(self):
        plurals = {'device_templates': 'device_template'}
        super(CLITestV10VmDeviceTemplateJSON, self).setUp(plurals=plurals)

    def test_create_device_template_all_params(self):
        cmd = device_template.CreateDeviceTemplate(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'my-name'
        description = 'my-description'
        service_type = 'MY-SERVICE'
        device_driver = 'device-driver'
        mgmt_driver = 'mgmt-driver'
        infra_driver = 'infra-driver'
        attr_key = 'attr-key'
        attr_val = 'attr-val'
        args = [
            '--name', name,
            '--description', description,
            '--template-service-type', service_type,
            '--device-driver', device_driver,
            '--mgmt-driver', mgmt_driver,
            '--infra-driver', infra_driver,
            '--attribute', attr_key, attr_val,
        ]
        position_names = ['name', 'description',
                          'device_driver', 'mgmt_driver',
                          'infra_driver']
        position_values = [name, description, device_driver,
                           mgmt_driver, infra_driver]
        extra_body = {
            'service_types': [{'service_type': service_type}],
            'attributes': {attr_key: attr_val},
        }
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    def test_create_device_template_with_mandatory_params(self):
        cmd = device_template.CreateDeviceTemplate(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        service_type = 'MY-SERVICE'
        device_driver = 'device-driver'
        mgmt_driver = 'mgmt-driver'
        infra_driver = 'infra-driver'
        args = [
            '--template-service-type', service_type,
            '--device-driver', device_driver,
            '--mgmt-driver', mgmt_driver,
            '--infra-driver', infra_driver,
        ]
        position_names = ['device_driver', 'mgmt_driver', 'infra_driver']
        position_values = [device_driver, mgmt_driver, infra_driver]
        extra_body = {
            'service_types': [{'service_type': service_type}],
        }
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    def test_list_device_templates(self):
        cmd = device_template.ListDeviceTemplate(test_cli10.MyApp(sys.stdout),
                                                 None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_list_device_templates_pagenation(self):
        cmd = device_template.ListDeviceTemplate(test_cli10.MyApp(sys.stdout),
                                                 None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_show_device_template_id(self):
        cmd = device_template.ShowDeviceTemplate(test_cli10.MyApp(sys.stdout),
                                                 None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id, args,
                                 ['id'])

    def test_show_device_template_id_name(self):
        cmd = device_template.ShowDeviceTemplate(test_cli10.MyApp(sys.stdout),
                                                 None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_device_template(self):
        cmd = device_template.UpdateDeviceTemplate(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'new-name'
        description = 'new-description'
        self._test_update_resource(self._RESOURCE, cmd, my_id,
                                   [my_id, '--name', name,
                                    '--description', description],
                                   {'name': name, 'description': description})

    def test_delete_device_tempalte(self):
        cmd = device_template.DeleteDeviceTemplate(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(self._RESOURCE, cmd, my_id, args)
