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

import ast
from unittest import mock

import fixtures
import yaml

from tackerclient.common import exceptions
from tackerclient.common import utils
from tackerclient.osc.v1.vnfm import vnf
from tackerclient.tests.unit.osc import base
from tackerclient.tests.unit.osc.v1.fixture_data import client


def _get_columns_vnf_parameter():

    columns = ['attributes', 'project_id']
    return columns


class TestVnfParameter(base.FixturedTestCase):
    client_fixture_class = client.ClientFixture

    def setUp(self):
        super(TestVnfParameter, self).setUp()
        self.url = client.TACKER_URL
        self.header = {'content-type': 'application/json'}
        self.app = mock.Mock()
        self.app_args = mock.Mock()
        self.client_manager = self.cs
        self.app.client_manager.tackerclient = self.client_manager


class TestUpdateVNF(TestVnfParameter):

    def setUp(self):
        super(TestUpdateVNF, self).setUp()
        self.useFixture(fixtures.MonkeyPatch(
            'tackerclient.tacker.v1_0.find_resourceid_by_name_or_id',
            self._find_resourceid))
        self.set_vnf = vnf.UpdateVNF(
            self.app, self.app_args, cmd_name='vnf set')

    def _find_resourceid(self, client, resource, name_or_id):
        return name_or_id

    def _cmd_parser(self, cmd_parser, sub_argv):
        _argv = sub_argv
        index = -1
        if '--' in sub_argv:
            index = sub_argv.index('--')
            _argv = sub_argv[:index]
        known_args, _values_specs = cmd_parser.parse_known_args(_argv)
        return known_args

    def _get_vnf_data(self, vnf_parameter):
        return tuple([vnf_parameter[key]
                     for key in sorted(vnf_parameter.keys())])

    def _take_action(self, args, extra_fields, get_client_called_count=1):
        cmd_par = self.set_vnf.get_parser("update_vnf")
        parsed_args = self._cmd_parser(cmd_par, args)
        body = {"vnf": extra_fields}
        body = str(body)
        project_id = {"tenant_id": "test-vnf-tenant_id"}
        extra_fields.update(project_id)
        json = {"vnf": extra_fields}

        self.requests_mock.register_uri(
            'PUT', self.url + '/v1.0/vnfs/my-id.json',
            json=json, headers=self.header)
        columns, data = (self.set_vnf.take_action(parsed_args))

        self.assertCountEqual(_get_columns_vnf_parameter(),
                              columns)
        self.assertEqual(get_client_called_count,
                         self.requests_mock.call_count)
        self.assertCountEqual(
            ast.literal_eval(self.requests_mock.last_request.body),
            ast.literal_eval(body))
        self.assertCountEqual(self._get_vnf_data(json['vnf']), data)

    def test_vnf_update_param_file(self):
        my_id = 'my-id'
        param_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_param.yaml')
        args = [my_id, '--param-file', str(param_file)]
        extra_fields = {'attributes': {'param_values': {'key': 'new-value'}}}

        self._take_action(args, extra_fields)

    def test_vnf_update_config_file(self):
        my_id = 'my-id'
        config_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_config.yaml')
        p_auth_url = 'http://1.2.3.4:5000'
        p_project_name = 'abc'
        p_username = 'xyz'
        p_project_domain_name = 'prj_domain_name'
        p_type = 'openstack'
        p_user_domain_name = 'user_domain_name'
        p_password = '12345'
        args = [my_id, '--config-file', str(config_file)]
        config = {'auth_url': p_auth_url, 'project_name': p_project_name,
                  'username': p_username,
                  'project_domain_name': p_project_domain_name,
                  'type': p_type, 'user_domain_name': p_user_domain_name,
                  'password': p_password}
        extra_fields = {'attributes': {'config': config}}

        self._take_action(args, extra_fields)

    def test_vnf_update_config(self):
        my_id = 'my-id'
        p_auth_url = 'https://1.2.3.4:6443'
        p_type = 'kubernetes'
        p_password = '12345'
        p_project_name = 'default'
        p_username = 'xyz'
        p_ssl_ca_cert = 'abcxyz'
        config = {'password': p_password, 'project_name': p_project_name,
                  'username': p_username, 'type': p_type,
                  'ssl_ca_cert': p_ssl_ca_cert, 'auth_url': p_auth_url}
        config = yaml.dump(config)
        args = [my_id, '--config', str(config)]
        extra_fields = {'attributes': {'config': config}}

        self._take_action(args, extra_fields)

    def test_vnf_update_invalid_format_param_file(self):
        my_id = 'my-id'
        param_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_invalid_format_param.yaml')
        args = [my_id, '--param-file', str(param_file)]
        extra_fields = {'attributes': {'param_values': None}}

        self.assertRaises(exceptions.InvalidInput,
                          self._take_action,
                          args, extra_fields)

    def test_vnf_update_empty_param_file(self):
        my_id = 'my-id'
        param_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_empty_param.yaml')
        args = [my_id, '--param-file', str(param_file)]
        extra_fields = {'attributes': {'param_values': None}}

        self.assertRaises(exceptions.InvalidInput,
                          self._take_action,
                          args, extra_fields)

    def test_vnf_update_invalid_format_config_file(self):
        my_id = 'my-id'
        config_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_invalid_format_config.yaml')
        args = [my_id, '--config-file', str(config_file)]
        extra_fields = {'attributes': {'config': None}}

        self.assertRaises(exceptions.InvalidInput,
                          self._take_action,
                          args, extra_fields)

    def test_vnf_update_empty_config_file(self):
        my_id = 'my-id'
        config_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_empty_config.yaml')
        args = [my_id, '--config-file', str(config_file)]
        extra_fields = {'attributes': {'config': None}}

        self.assertRaises(exceptions.InvalidInput,
                          self._take_action,
                          args, extra_fields)

    def test_vnf_update_invalid_format_config(self):
        my_id = 'my_id'
        config = 'test: : ]['
        args = [my_id, '--config', config]
        extra_fields = {'attributes': {'config': None}}

        self.assertRaises(exceptions.InvalidInput,
                          self._take_action,
                          args, extra_fields)

    def test_vnf_update_empty_config(self):
        my_id = 'my-id'
        config = ' '
        args = [my_id, '--config', config]
        extra_fields = {'attributes': {'config': None}}

        self.assertRaises(exceptions.InvalidInput,
                          self._take_action,
                          args, extra_fields)

    def test_vnf_update_multi_args_config_configfile_paramfile(self):
        my_id = 'my-id'
        config_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_config.yaml')
        param_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_param.yaml')
        p_auth_url = 'https://1.2.3.4:6443'
        p_type = 'kubernetes'
        p_password = '12345'
        p_project_name = 'default'
        p_username = 'xyz'
        p_ssl_ca_cert = 'abcxyz'
        config = {'password': p_password, 'project_name': p_project_name,
                  'username': p_username, 'type': p_type,
                  'ssl_ca_cert': p_ssl_ca_cert, 'auth_url': p_auth_url}
        config = yaml.dump(config)
        args = [my_id, '--config-file', str(config_file),
                '--config', str(config), '--param-file', str(param_file)]
        extra_fields = {'attributes': None}

        self.assertRaises(BaseException,
                          self._take_action,
                          args, extra_fields)

    def test_vnf_update_multi_args_configfile_paramfile(self):
        my_id = 'my-id'
        config_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_config.yaml')
        param_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_param.yaml')
        args = [my_id, '--param-file', str(param_file),
                '--config-file', str(config_file)]
        extra_fields = {'attributes': None}

        self.assertRaises(BaseException,
                          self._take_action,
                          args, extra_fields)

    def test_vnf_update_multi_args_config_configfile(self):
        my_id = 'my-id'
        config_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_config.yaml')
        p_auth_url = 'https://1.2.3.4:6443'
        p_type = 'kubernetes'
        p_password = '12345'
        p_project_name = 'default'
        p_username = 'xyz'
        p_ssl_ca_cert = 'abcxyz'
        config = {'password': p_password, 'project_name': p_project_name,
                  'username': p_username, 'type': p_type,
                  'ssl_ca_cert': p_ssl_ca_cert, 'auth_url': p_auth_url}
        config = yaml.dump(config)
        args = [my_id, '--config-file', str(config_file),
                '--config', str(config)]
        extra_fields = {'attributes': None}

        self.assertRaises(BaseException,
                          self._take_action,
                          args, extra_fields)

    def test_vnf_update_multi_args_config_paramfile(self):
        my_id = 'my-id'
        param_file = utils.get_file_path(
            'tests/unit/osc/samples/vnf_update_param.yaml')
        p_auth_url = 'https://1.2.3.4:6443'
        p_type = 'kubernetes'
        p_password = '12345'
        p_project_name = 'default'
        p_username = 'xyz'
        p_ssl_ca_cert = 'abcxyz'
        config = {'password': p_password, 'project_name': p_project_name,
                  'username': p_username, 'type': p_type,
                  'ssl_ca_cert': p_ssl_ca_cert, 'auth_url': p_auth_url}
        config = yaml.dump(config)
        args = [my_id, '--param-file', str(param_file),
                '--config', str(config)]
        extra_fields = {'attributes': None}

        self.assertRaises(BaseException,
                          self._take_action,
                          args, extra_fields)

    def test_vnf_update_param_file_with_empty_dict(self):
        my_id = 'my-id'
        param_file = utils.get_file_path(
            'tests/unit/osc/samples/'
            'vnf_update_param_file_with_empty_dict.yaml')
        args = [my_id, '--param-file', str(param_file)]
        extra_fields = {'attributes': None}

        self.assertRaises(exceptions.InvalidInput,
                          self._take_action,
                          args, extra_fields)

    def test_vnf_update_config_file_with_empty_dict(self):
        my_id = 'my-id'
        config_file = utils.get_file_path(
            'tests/unit/osc/samples/'
            'vnf_update_config_file_with_empty_dict.yaml')
        args = [my_id, '--config-file', str(config_file)]
        extra_fields = {'attributes': None}

        self.assertRaises(exceptions.InvalidInput,
                          self._take_action,
                          args, extra_fields)
