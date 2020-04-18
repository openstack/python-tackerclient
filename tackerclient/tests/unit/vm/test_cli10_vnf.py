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
from unittest import mock

from tackerclient.common import exceptions
from tackerclient.common import utils
from tackerclient import shell
from tackerclient.tacker import v1_0 as tackerV1_0
from tackerclient.tacker.v1_0 import TackerCommand
from tackerclient.tacker.v1_0.vnfm import vnf
from tackerclient.tests.unit import test_cli10
from tackerclient.tests.unit import test_utils

API_VERSION = "1.0"
FORMAT = 'json'
TOKEN = 'testtoken'
ENDURL = 'localurl'


class CLITestV10VmVNFJSON(test_cli10.CLITestV10Base):
    _RESOURCE = 'vnf'
    _RESOURCES = 'vnfs'
    _VNF_RESOURCES = 'vnf_resources'

    def setUp(self):
        plurals = {'vnfs': 'vnf',
                   'resources': 'resource'}
        super(CLITestV10VmVNFJSON, self).setUp(plurals=plurals)

    @mock.patch.object(TackerCommand, 'get_client')
    def _test_create_resource(self, resource, cmd, name, myid, args,
                              position_names, position_values, mock_get,
                              tenant_id=None, tags=None, admin_state_up=True,
                              extra_body=None, **kwargs):
        mock_get.return_value = self.client
        non_admin_status_resources = ['vnfd', 'vnf']
        if (resource in non_admin_status_resources):
            body = {resource: {}, }
        else:
            body = {resource: {'admin_state_up': admin_state_up, }, }
        if tenant_id:
            body[resource].update({'tenant_id': tenant_id})
        if tags:
            body[resource].update({'tags': tags})
        if extra_body:
            body[resource].update(extra_body)
        body[resource].update(kwargs)

        for i in range(len(position_names)):
            body[resource].update({position_names[i]: position_values[i]})
        ress = {resource:
                {self.id_field: myid}, }
        if name:
            ress[resource].update({'name': name})
        self.client.format = self.format
        resstr = self.client.serialize(ress)
        # url method body
        resource_plural = tackerV1_0._get_resource_plural(resource,
                                                          self.client)
        path = getattr(self.client, resource_plural + "_path")
        # Work around for LP #1217791. XML deserializer called from
        # MyComparator does not decodes XML string correctly.
        if self.format == 'json':
            _body = test_cli10.MyComparator(body, self.client)
        else:
            _body = self.client.serialize(body)
        with mock.patch.object(self.client.httpclient, 'request') as mock_req:
            mock_req.return_value = (test_cli10.MyResp(200), resstr)
            args.extend(['--request-format', self.format])
            args.extend(['--vnfd-id', 'vnfd'])
            cmd_parser = cmd.get_parser('create_' + resource)
            shell.run_command(cmd, cmd_parser, args)
            mock_req.assert_called_once_with(
                test_cli10.end_url(path, format=self.format), 'POST',
                body=_body,
                headers=test_utils.ContainsKeyValue('X-Auth-Token', TOKEN))
        mock_get.assert_any_call()

    def test_create_vnf_all_params(self):
        cmd = vnf.CreateVNF(test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        vnfd_id = 'vnfd'
        vim_id = 'vim_id'
        description = 'my-description'
        region_name = 'region'
        key = 'key'
        value = 'value'

        args = [
            name,
            '--vnfd-id', vnfd_id,
            '--vim-id', vim_id,
            '--description', description,
            '--vim-region-name', region_name,
            '--%s' % key, value]
        position_names = [
            'name',
            'vnfd_id',
            'vim_id',
            'description',
            'attributes',
        ]
        position_values = [
            name,
            vnfd_id,
            vim_id,
            description,
            {},
        ]
        extra_body = {key: value, 'placement_attr': {'region_name':
                                                     region_name}}
        self._test_create_resource(self._RESOURCE, cmd, name, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    def test_create_vnf_with_vnfd_id(self):
        cmd = vnf.CreateVNF(test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        vnfd_id = 'vnfd'
        args = [
            name,
            '--vnfd-id', vnfd_id,
        ]
        position_names = ['name', 'vnfd_id', 'attributes']
        position_values = [name, vnfd_id, {}]
        self._test_create_resource(self._RESOURCE, cmd, name, my_id,
                                   args, position_names, position_values)

    def test_create_vnf_with_description_param(self):
        cmd = vnf.CreateVNF(test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        vnfd_id = 'vnfd'
        description = 'my-description'
        args = [
            name,
            '--vnfd-id', vnfd_id,
            '--description', description,
        ]
        position_names = ['name', 'vnfd_id', 'description',
                          'attributes']
        position_values = [name, vnfd_id, description, {}]
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values)

    def test_list_vnfs(self):
        cmd = vnf.ListVNF(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_list_vnfs_pagenation(self):
        cmd = vnf.ListVNF(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_show_vnf_id(self):
        cmd = vnf.ShowVNF(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id, args,
                                 ['id'])

    def test_show_vnf_id_name(self):
        cmd = vnf.ShowVNF(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_vnf(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        key = 'new_key'
        value = 'new-value'
        self._test_update_resource(self._RESOURCE, cmd, my_id,
                                   [my_id, '--%s' % key, value],
                                   {key: value})

    def test_vnf_update_param_file(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        key = 'key'
        value = 'new-value'
        config_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_param.yaml')
        args = [my_id, '--param-file', str(config_file)]
        extra_fields = {'attributes': {'param_values': {key: value}}}

        self._test_update_resource(self._RESOURCE, cmd, my_id, args,
                                   extra_fields)

    def test_vnf_update_config_file(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        name = 'my-name'
        description = 'Vim Description'
        vim_config = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_config.yaml')
        args = [
            name,
            '--config-file', vim_config,
            '--description', description]
        p_auth_url = 'http://1.2.3.4:5000'
        p_type = 'openstack'
        p_project_name = 'abc'
        p_username = 'xyz'
        p_project_domain_name = 'prj_domain_name'
        p_user_domain_name = 'user_domain_name'
        p_password = '12345'
        config = {'auth_url': p_auth_url, 'project_name': p_project_name,
                  'username': p_username,
                  'project_domain_name': p_project_domain_name,
                  'type': p_type, 'user_domain_name': p_user_domain_name,
                  'password': p_password}
        extra_body = {'description': description,
                      'attributes': {'config': config}}

        self._test_update_resource(self._RESOURCE, cmd, name, args, extra_body)

    def test_vnf_update_config(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        name = 'my-name'
        description = 'Vim Description'
        p_auth_url = 'https://1.2.3.4:6443'
        p_type = 'kubernetes'
        p_password = '12345'
        p_project_name = 'default'
        p_username = 'xyz'
        p_ssl_ca_cert = 'abcxyz'
        config = {'password': p_password, 'project_name': p_project_name,
                  'username': p_username, 'type': p_type,
                  'ssl_ca_cert': p_ssl_ca_cert, 'auth_url': p_auth_url}
        args = [
            name,
            '--description', description,
            '--config', str(config)]
        extra_body = {'description': description,
                      'attributes': {'config': config}}

        self._test_update_resource(self._RESOURCE, cmd, name, args, extra_body)

    def test_vnf_update_invalid_format_param_file(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'my-name'
        key = 'key'
        value = 'new-value'
        config_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_invalid_format_param.yaml')
        args = [my_id, '--param-file', str(config_file)]
        extra_fields = {'attributes': {'param_values': {key: value}}}

        self.assertRaises(exceptions.InvalidInput,
                          self._test_update_resource,
                          self._RESOURCE, cmd, name, args, extra_fields)

    def test_vnf_update_empty_param_file(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'my-name'
        key = 'key'
        value = 'new-value'
        config_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_empty_param.yaml')
        args = [my_id, '--param-file', str(config_file)]
        extra_fields = {'attributes': {'param_values': {key: value}}}

        self.assertRaises(exceptions.InvalidInput,
                          self._test_update_resource,
                          self._RESOURCE, cmd, name, args, extra_fields)

    def test_vnf_update_invalid_format_config_file(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        name = 'my-name'
        description = 'Vim Description'
        vim_config = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_invalid_format_config.yaml')
        args = [
            name,
            '--config-file', vim_config,
            '--description', description]
        p_auth_url = 'http://1.2.3.4:5000'
        p_type = 'openstack'
        p_project_name = 'abc'
        p_username = 'xyz'
        p_project_domain_name = 'prj_domain_name'
        p_user_domain_name = 'user_domain_name'
        p_password = '12345'
        config = {'auth_url': p_auth_url, 'project_name': p_project_name,
                  'username': p_username,
                  'project_domain_name': p_project_domain_name, 'type': p_type,
                  'user_domain_name': p_user_domain_name,
                  'password': p_password}
        extra_body = {'description': description,
                      'attributes': {'config': config}}

        self.assertRaises(exceptions.InvalidInput,
                          self._test_update_resource,
                          self._RESOURCE, cmd, name, args, extra_body)

    def test_vnf_update_empty_config_file(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        name = 'my-name'
        description = 'Vim Description'
        vim_config = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_empty_config.yaml')
        args = [
            name,
            '--config-file', vim_config,
            '--description', description]
        extra_body = {'description': description}

        self.assertRaises(exceptions.InvalidInput,
                          self._test_update_resource,
                          self._RESOURCE, cmd, name, args, extra_body)

    def test_vnf_update_invalid_format_config(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'vnfs/my-id'
        key = 'key'
        value = 'new-value'
        description = 'Vim Description'
        extra_fields = {'attributes': {'param_values': {key: value}}}
        config = 'test: : ]['
        args = [my_id,
                '--config', config,
                '--description', description]

        self.assertRaises(exceptions.InvalidInput,
                          self._test_update_resource,
                          self._RESOURCE, cmd, name, args, extra_fields)

    def test_vnf_update_empty_config(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        name = 'my-name'
        description = 'Vim Description'
        config = {}
        args = [name,
                '--config', str(config),
                '--description', description]
        extra_body = {'description': description}

        self.assertRaises(exceptions.InvalidInput,
                          self._test_update_resource,
                          self._RESOURCE, cmd, name, args, extra_body)

    def test_vnf_update_multi_args_config_configfile_paramfile(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        key = 'key'
        name = 'my-name'
        value = 'new-value'
        description = 'Vim Description'
        p_auth_url = 'https://1.2.3.4:6443'
        p_type = 'kubernetes'
        p_password = '12345'
        p_project_name = 'default'
        p_username = 'xyz'
        p_ssl_ca_cert = 'abcxyz'
        config = {'password': p_password, 'project_name': p_project_name,
                  'username': p_username, 'type': p_type,
                  'ssl_ca_cert': p_ssl_ca_cert, 'auth_url': p_auth_url}
        vim_config = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_config.yaml')
        param_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_param.yaml')
        args = [my_id,
                '--config-file', str(vim_config),
                '--param-file', str(param_file),
                '--config', str(config),
                '--description', description]
        extra_fields = {'attributes': {'param_values': {key: value}}}

        self.assertRaises(BaseException,
                          self._test_update_resource,
                          self._RESOURCE, cmd, name, args, extra_fields)

    def test_vnf_update_multi_args_configfile_paramfile(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        description = 'Vim Description'
        param_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_param.yaml')
        vim_config = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_config.yaml')
        args = [
            my_id,
            '--param-file', str(param_file),
            '--config-file', vim_config,
            '--description', description]
        extra_body = {'description': description}

        self.assertRaises(BaseException,
                          self._test_update_resource,
                          self._RESOURCE, cmd, name, args, extra_body)

    def test_vnf_update_multi_args_config_configfile(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        description = 'Vim Description'
        p_auth_url = 'https://1.2.3.4:6443'
        p_type = 'kubernetes'
        p_password = '12345'
        p_project_name = 'default'
        p_username = 'xyz'
        p_ssl_ca_cert = 'abcxyz'
        config = {'password': p_password, 'project_name': p_project_name,
                  'username': p_username, 'type': p_type,
                  'ssl_ca_cert': p_ssl_ca_cert, 'auth_url': p_auth_url}
        vim_config = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_config.yaml')
        args = [
            my_id,
            '--config-file', str(vim_config),
            '--config', str(config),
            '--description', description]
        extra_body = {'description': description}

        self.assertRaises(BaseException,
                          self._test_update_resource,
                          self._RESOURCE, cmd, name, args, extra_body)

    def test_vnf_update_multi_args_config_paramfile(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        description = 'Vim Description'
        p_auth_url = 'https://1.2.3.4:6443'
        p_type = 'kubernetes'
        p_password = '12345'
        p_project_name = 'default'
        p_username = 'xyz'
        p_ssl_ca_cert = 'abcxyz'
        config = {'password': p_password, 'project_name': p_project_name,
                  'username': p_username, 'type': p_type,
                  'ssl_ca_cert': p_ssl_ca_cert, 'auth_url': p_auth_url}
        param_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_param.yaml')
        args = [
            my_id,
            '--param-file', str(param_file),
            '--config', str(config),
            '--description', description]
        extra_body = {'description': description}

        self.assertRaises(BaseException,
                          self._test_update_resource,
                          self._RESOURCE, cmd, name, args, extra_body)

    def test_vnf_update_param_file_with_empty_dict(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'my-name'
        key = 'key'
        value = 'new-value'
        config_file = utils.get_file_path(
            'tests/unit/osc/samples/'
            'vnf_update_param_file_with_empty_dict.yaml')
        args = [my_id, '--param-file', str(config_file)]
        extra_fields = {'attributes': {'param_values': {key: value}}}

        self.assertRaises(exceptions.InvalidInput,
                          self._test_update_resource,
                          self._RESOURCE, cmd, name, args, extra_fields)

    def test_vnf_update_config_file_with_empty_dict(self):
        cmd = vnf.UpdateVNF(test_cli10.MyApp(sys.stdout), None)
        name = 'my-name'
        description = 'Vim Description'
        vim_config = utils.get_file_path(
            'tests/unit/osc/samples/'
            'vnf_update_config_file_with_empty_dict.yaml')
        args = [
            name,
            '--config-file', vim_config,
            '--description', description]
        extra_body = {'description': description}

        self.assertRaises(exceptions.InvalidInput,
                          self._test_update_resource,
                          self._RESOURCE, cmd, name, args, extra_body)

    def test_delete_vnf(self):
        cmd = vnf.DeleteVNF(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(self._RESOURCE, cmd, my_id, args)

    def test_delete_vnf_with_force(self):
        cmd = vnf.DeleteVNF(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id, '--force']
        self._test_delete_resource(self._RESOURCE, cmd, my_id, args)

    def test_list_vnf_resources(self):
        cmd = vnf.ListVNFResources(test_cli10.MyApp(sys.stdout), None)
        base_args = [self.test_id]
        response = [{'name': 'CP11', 'id': 'id1', 'type': 'NeutronPort'},
                    {'name': 'CP12', 'id': 'id2', 'type': 'NeutronPort'}]
        val = self._test_list_sub_resources(self._VNF_RESOURCES, 'resources',
                                            cmd, self.test_id,
                                            response_contents=response,
                                            detail=True, base_args=base_args)
        self.assertIn('id1', val)
        self.assertIn('NeutronPort', val)
        self.assertIn('CP11', val)

    def test_multi_delete_vnf(self):
        cmd = vnf.DeleteVNF(test_cli10.MyApp(sys.stdout), None)
        vnf_ids = 'vnf1 vnf2 vnf3'
        args = [vnf_ids]
        self._test_delete_resource(self._RESOURCE, cmd, vnf_ids, args)
