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

from tackerclient.tacker.v1_0.vm import service_instance
from tackerclient.tests.unit import test_cli10


class CLITestV10VmServiceInstanceJSON(test_cli10.CLITestV10Base):
    _RESOURCE = 'service_instance'
    _RESOURCES = 'service_instances'

    def setUp(self):
        plurals = {'service_instances': 'service_instance'}
        super(CLITestV10VmServiceInstanceJSON, self).setUp(plurals=plurals)

    def test_create_service_instance_all_params(self):
        cmd = service_instance.CreateServiceInstance(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'my-name'
        service_type_id = 'service-type-id'
        service_table_id = 'service-table-id'
        mgmt_driver = 'mgmt-driver'
        network_id = 'network_id'
        subnet_id = 'subnet_id'
        port_id = 'port_id'
        router_id = 'router_id'
        role = 'role'
        index = 1

        device = 'my-device'

        key = 'key'
        value = 'value'

        args = [
            '--name', name,
            '--service-type-id', service_type_id,
            '--service-table-id', service_table_id,
            '--mgmt-driver', mgmt_driver,
            '--service-context',
            ('network-id=%s,subnet-id=%s,port-id=%s,router-id=%s,'
             'role=%s,index=%s' % (network_id, subnet_id, port_id, router_id,
                                   role, index)),
            '--device', device,
            '--kwargs', '%s=%s' % (key, value),
        ]
        position_names = ['name', 'service_type_id', 'service_table_id',
                          'mgmt_driver']
        position_values = [name, service_type_id, service_table_id,
                           mgmt_driver]
        extra_body = {
            'devices': [device],
            'service_context': [{
                'network_id': network_id,
                'subnet_id': subnet_id,
                'port_id': port_id,
                'router_id': router_id,
                'role': role,
                'index': str(index),
            }],
            'kwargs': {
                key: value
            },
        }
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    def test_create_service_instance_with_mandatory_params(self):
        cmd = service_instance.CreateServiceInstance(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        service_type_id = 'service-type-id'
        service_table_id = 'service-table-id'
        device = 'my-device'
        args = [
            '--service-type-id', service_type_id,
            '--service-table-id', service_table_id,
            '--device', device,
        ]
        position_names = ['service_type_id', 'service_table_id']
        position_values = [service_type_id, service_table_id]
        extra_body = {
            'devices': [device],
        }
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    def test_list_service_instances(self):
        cmd = service_instance.ListServiceInstance(
            test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_list_service_instances_pagenation(self):
        cmd = service_instance.ListServiceInstance(
            test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_show_service_instance_id(self):
        cmd = service_instance.ShowServiceInstance(
            test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id, args,
                                 ['id'])

    def test_show_service_instance_id_name(self):
        cmd = service_instance.ShowServiceInstance(
            test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_service_instance(self):
        cmd = service_instance.UpdateServiceInstance(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        key = 'new-key'
        value = 'new-value'
        self._test_update_resource(self._RESOURCE, cmd, my_id,
                                   [my_id, '--kwargs', '%s=%s' % (key, value)],
                                   {'kwargs': {key: value}})

    def test_delete_service_instance(self):
        cmd = service_instance.DeleteServiceInstance(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(self._RESOURCE, cmd, my_id, args)


class CLITestV10VmServiceInstanceXML(CLITestV10VmServiceInstanceJSON):
    format = 'xml'
