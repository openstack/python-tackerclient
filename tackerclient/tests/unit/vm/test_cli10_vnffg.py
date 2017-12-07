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

from tackerclient.common import utils
from tackerclient.tacker.v1_0.nfvo import vnffg
from tackerclient.tests.unit import test_cli10

API_VERSION = "1.0"
FORMAT = 'json'
TOKEN = 'testtoken'
ENDURL = 'localurl'


class CLITestV10VmVNFFGJSON(test_cli10.CLITestV10Base):
    _RESOURCE = 'vnffg'
    _RESOURCES = 'vnffgs'

    def setUp(self):
        plurals = {'vnffgs': 'vnffg'}
        super(CLITestV10VmVNFFGJSON, self).setUp(plurals=plurals)

    def test_create_vnffg_all_params(self):
        cmd = vnffg.CreateVNFFG(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        vnffgd_id = 'vnffgd'
        vnffg_name = 'fake-vnffg'
        vnf_mapping = 'VNFD1:VNF1'

        args = [
            vnffg_name,
            '--vnffgd-id', vnffgd_id,
            '--vnf-mapping', vnf_mapping,
            '--symmetrical']
        position_names = ['vnffgd_id', 'vnf_mapping', 'symmetrical']
        position_values = [vnffgd_id, {"VNFD1": "VNF1"}, True]
        extra_body = {'name': vnffg_name, 'attributes': {}}
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body,
                                   get_client_called_count=2)

    def test_create_vnffg_with_mandatory_params(self):
        cmd = vnffg.CreateVNFFG(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        vnffg_name = 'fake-vnffg'
        vnffgd_id = 'vnffgd'
        args = [
            vnffg_name,
            '--vnffgd-id', vnffgd_id,
        ]
        position_names = ['vnffgd_id']
        position_values = [vnffgd_id]
        extra_body = {'symmetrical': False, 'name': vnffg_name,
                      'attributes': {}}
        self._test_create_resource(self._RESOURCE, cmd, vnffg_name, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body,
                                   get_client_called_count=2)

    def test_list_vnffgs(self):
        cmd = vnffg.ListVNFFG(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_list_vnffgs_pagenation(self):
        cmd = vnffg.ListVNFFG(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_show_vnffg_id(self):
        cmd = vnffg.ShowVNFFG(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id, args,
                                 ['id'])

    def test_show_vnffg_id_name(self):
        cmd = vnffg.ShowVNFFG(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_vnffg(self):
        cmd = vnffg.UpdateVNFFG(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        update_vnffg = utils.get_file_path(
            'tests/unit/vm/samples/vnffg_update_file.yaml')
        vnf_mapping = 'VNFD1:VNF1'
        args = [
            my_id,
            '--vnf-mapping', vnf_mapping,
            '--vnffgd-template', str(update_vnffg),
            '--symmetrical'
        ]
        extra_fields = {
            "vnf_mapping": {"VNFD1": "VNF1"},
            "vnffgd_template": "abcxyz",
            "symmetrical": True
        }
        self._test_update_resource(self._RESOURCE, cmd, my_id,
                                   args, extra_fields,
                                   get_client_called_count=2)

    def test_delete_vnffg(self):
        cmd = vnffg.DeleteVNFFG(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(self._RESOURCE, cmd, my_id, args)
