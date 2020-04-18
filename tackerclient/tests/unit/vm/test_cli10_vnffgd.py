# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys

from tackerclient.tacker.v1_0.nfvo import vnffgd
from tackerclient.tests.unit import test_cli10
from unittest.mock import mock_open
from unittest.mock import patch


class CLITestV10VmVNFFGDJSON(test_cli10.CLITestV10Base):
    _RESOURCE = 'vnffgd'
    _RESOURCES = 'vnffgds'

    def setUp(self):
        plurals = {'vnffgds': 'vnffgd'}
        super(CLITestV10VmVNFFGDJSON, self).setUp(plurals=plurals)

    @patch("tackerclient.tacker.v1_0.nfvo.vnffgd.open",
           side_effect=mock_open(read_data="vnffgd"),
           create=True)
    def test_create_vnffgd_all_params(self, mo):
        cmd = vnffgd.CreateVNFFGD(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'my-name'
        attr_key = 'vnffgd'
        attr_val = 'vnffgd'
        description = 'vnffgd description'
        args = [
            name,
            '--vnffgd-file', 'vnffgd_file',
            '--description', description,
        ]
        position_names = ['name', 'description']
        position_values = [name, description]
        extra_body = {
            'template': {attr_key: attr_val},
        }

        self._test_create_resource(self._RESOURCE, cmd, name, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    @patch("tackerclient.tacker.v1_0.nfvo.vnffgd.open",
           side_effect=mock_open(read_data="vnffgd"),
           create=True)
    def test_create_vnffgd_with_mandatory_params(self, mo):
        cmd = vnffgd.CreateVNFFGD(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'my-name'
        attr_key = 'vnffgd'
        attr_val = 'vnffgd'
        args = [
            name,
            '--vnffgd-file', 'vnffgd_file',
        ]
        position_names = ['name']
        position_values = [name]
        extra_body = {
            'template': {attr_key: attr_val},
        }

        self._test_create_resource(self._RESOURCE, cmd, name, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    def test_list_vnffgds(self):
        cmd = vnffgd.ListVNFFGD(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True,
                                  template_source='onboarded')

    def test_list_inline_vnffgds(self):
        cmd = vnffgd.ListVNFFGD(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True,
                                  template_source='inline')

    def test_list_all_vnffgds(self):
        cmd = vnffgd.ListVNFFGD(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True,
                                  template_source='all')

    def test_list_vnffgds_pagenation(self):
        cmd = vnffgd.ListVNFFGD(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True,
                                  template_source='onboarded')

    def test_show_vnffgd_id(self):
        cmd = vnffgd.ShowVNFFGD(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id, args,
                                 ['id'])

    def test_show_vnffgd_id_name(self):
        cmd = vnffgd.ShowVNFFGD(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_delete_vnffgd(self):
        cmd = vnffgd.DeleteVNFFGD(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(self._RESOURCE, cmd, my_id, args)
