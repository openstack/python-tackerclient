# Copyright 2015-2016 Brocade Communications Systems Inc
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

import mox

from tackerclient.tacker.v1_0.nfvo import vim
from tackerclient.tests.unit import test_cli10

API_VERSION = "1.0"
FORMAT = 'json'
TOKEN = 'testtoken'
ENDURL = 'localurl'


class CLITestV10VIMJSON(test_cli10.CLITestV10Base):
    _RESOURCE = 'vim'
    _RESOURCES = 'vims'

    def setUp(self):
        plurals = {'vims': 'vim'}
        super(CLITestV10VIMJSON, self).setUp(plurals=plurals)
        self.vim_project = {'name': 'abc', 'id': ''}
        self.auth_cred = {'username': 'xyz', 'password': '12345', 'user_id':
                          ''}
        self.auth_url = 'http://1.2.3.4:5000'

    def test_register_vim_all_params(self):
        cmd = vim.CreateVIM(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'test_vim'
        description = 'Vim Description'
        vim_config = {'auth_url': 'http://1.2.3.4:5000', 'username': 'xyz',
                      'password': '12345', 'project_name': 'abc'}
        args = [
            '--config', str(vim_config),
            '--name', name,
            '--description', description]
        position_names = ['auth_cred', 'vim_project', 'auth_url']
        position_values = [self.auth_cred, self.vim_project, self.auth_url]
        extra_body = {'type': 'openstack', 'name': name, 'description':
                      description}
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    def test_register_vim_with_mandatory_params(self):
        cmd = vim.CreateVIM(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'

        vim_config = {'auth_url': 'http://1.2.3.4:5000', 'username': 'xyz',
                      'password': '12345', 'project_name': 'abc'}
        args = [
            '--config', str(vim_config),
        ]
        position_names = ['auth_cred', 'vim_project', 'auth_url']
        position_values = [self.auth_cred, self.vim_project, self.auth_url]
        extra_body = {'type': 'openstack'}
        self._test_create_resource(self._RESOURCE, cmd, None, my_id, args,
                                   position_names, position_values,
                                   extra_body=extra_body)

    def test_list_vims(self):
        cmd = vim.ListVIM(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def _test_list_vims_extend(self, data, expected_data, args=['-f', 'json']):
        resp_str = self.client.serialize({self._RESOURCES: data})
        resp = (test_cli10.MyResp(200), resp_str)
        cmd = vim.ListVIM(
            test_cli10.MyApp(sys.stdout), None)
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")

        cmd.get_client().MultipleTimes().AndReturn(self.client)
        path = getattr(self.client, self._RESOURCES + '_path')
        self.client.httpclient.request(test_cli10.MyUrlComparator(
            test_cli10.end_url(path, format=self.format), self.client),
            'GET', body=None, headers=mox.ContainsKeyValue(
                'X-Auth-Token', test_cli10.TOKEN)).AndReturn(resp)
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser("list_" + self._RESOURCES)
        parsed_args = cmd_parser.parse_args(args)
        result = cmd.take_action(parsed_args)
        res_data = [res for res in result[1]]
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
        for res, exp in zip(res_data, expected_data):
            self.assertEqual(len(exp), len(res))
            self.assertEqual(exp, res)

    def test_list_vims_extend(self):
        vim_data = [{'id': 'my_id1', 'auth_cred': {'password':
                     'encrypted_pw'}}, {'id': 'my_id2', 'auth_cred': {
                                        'password': 'another_encrypted_pw'}}]
        expected_data = [('my_id1', {'password': '***'}),
                         ('my_id2', {'password': '***'})]
        self._test_list_vims_extend(vim_data, expected_data)

    def test_show_vim_id(self):
        cmd = vim.ShowVIM(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id, args,
                                 ['id'])

    def test_show_vim_id_name(self):
        cmd = vim.ShowVIM(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_vim(self):
        cmd = vim.UpdateVIM(test_cli10.MyApp(sys.stdout), None)
        update_config = {'username': 'xyz', 'password': '12345',
                         'project_name': 'abc'}
        my_id = 'my-id'
        key = 'config'
        value = str(update_config)
        extra_fields = {'vim_project': self.vim_project, 'auth_cred':
                        self.auth_cred}
        self._test_update_resource(self._RESOURCE, cmd, my_id, [my_id,
                                                                '--%s' %
                                                                key, value],
                                   extra_fields)

    def test_delete_vim(self):
        cmd = vim.DeleteVIM(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(self._RESOURCE, cmd, my_id, args)
