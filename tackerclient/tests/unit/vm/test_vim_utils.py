# Copyright 2016 OpenStack Foundation.
# All Rights Reserved.
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

import testtools

from tackerclient.common import exceptions
from tackerclient.tacker.v1_0.nfvo import vim_utils
from unittest.mock import sentinel


class TestVIMUtils(testtools.TestCase):

    def test_args2body_vim(self):
        config_param = {'project_name': sentinel.prj_name,
                        'username': sentinel.usrname1,
                        'password': sentinel.password1,
                        'project_domain_name': sentinel.prj_domain_name1,
                        'user_domain_name': sentinel.user_domain.name,
                        'cert_verify': 'True',
                        'type': 'openstack'}
        vim = {}
        auth_cred = config_param.copy()
        auth_cred.pop('project_name')
        auth_cred.pop('project_domain_name')
        auth_cred.pop('type')
        expected_vim = {'auth_cred': auth_cred,
                        'vim_project':
                            {'name': sentinel.prj_name,
                             'project_domain_name': sentinel.prj_domain_name1},
                        'type': 'openstack'}
        vim_utils.args2body_vim(config_param.copy(), vim)
        self.assertEqual(expected_vim, vim)

    def test_args2body_vim_extra(self):
        auth_cred = {'username': sentinel.usrname1,
                     'password': sentinel.password1,
                     'user_domain_name': sentinel.user_domain.name,
                     'cert_verify': 'True'}
        config_param = {'project_name': sentinel.prj_name,
                        'project_domain_name': sentinel.prj_domain_name1,
                        'type': 'openstack',
                        'extra': {'area': 'area_A@region_A'},
                        **auth_cred}
        vim = {}

        expected_vim = {'auth_cred': auth_cred,
                        'vim_project':
                            {'name': sentinel.prj_name,
                             'project_domain_name': sentinel.prj_domain_name1},
                        'type': 'openstack',
                        'extra': {'area': 'area_A@region_A'}}

        vim_utils.args2body_vim(config_param.copy(), vim)
        self.assertEqual(expected_vim, vim)

    def test_args2body_kubernetes_vim(self):
        config_param = {'username': sentinel.usrname1,
                        'password': sentinel.password1,
                        'ssl_ca_cert': 'abcxyz',
                        'project_name': sentinel.prj_name,
                        'type': 'kubernetes'}
        vim = {}
        auth_cred = config_param.copy()
        auth_cred.pop('project_name')
        auth_cred.pop('type')
        expected_vim = {'auth_cred': auth_cred,
                        'vim_project':
                            {'name': sentinel.prj_name},
                        'type': 'kubernetes'}
        vim_utils.args2body_vim(config_param.copy(), vim)
        self.assertEqual(expected_vim, vim)

    def test_args2body_kubernetes_vim_bearer(self):
        config_param = {'bearer_token': sentinel.bearer_token,
                        'ssl_ca_cert': "None",
                        'project_name': sentinel.prj_name,
                        'type': 'kubernetes'}
        vim = {}
        auth_cred = config_param.copy()
        auth_cred.pop('project_name')
        auth_cred.pop('type')
        expected_vim = {'auth_cred': auth_cred,
                        'vim_project':
                            {'name': sentinel.prj_name},
                        'type': 'kubernetes'}
        vim_utils.args2body_vim(config_param.copy(), vim)
        self.assertEqual(expected_vim, vim)

    def test_args2body_kubernetes_vim_oidc(self):
        config_param = {'oidc_token_url': sentinel.oidc_token_url,
                        'username': sentinel.username,
                        'password': sentinel.password,
                        'client_id': sentinel.client_id,
                        'client_secret': sentinel.client_secret,
                        'ssl_ca_cert': "None",
                        'project_name': sentinel.prj_name,
                        'type': 'kubernetes'}
        vim = {}
        auth_cred = config_param.copy()
        auth_cred.pop('project_name')
        auth_cred.pop('type')
        expected_vim = {'auth_cred': auth_cred,
                        'vim_project':
                            {'name': sentinel.prj_name},
                        'type': 'kubernetes'}
        vim_utils.args2body_vim(config_param.copy(), vim)
        self.assertEqual(expected_vim, vim)

    def test_args2body_kubernetes_vim_extra(self):
        extra_param = {
            'helm_info': {
                'masternode_ip': [
                    '192.168.10.110'
                ],
                'masternode_username': 'helm_user',
                'masternode_password': 'helm_pass'
            }}

        config_param = {'username': sentinel.usrname1,
                        'password': sentinel.password1,
                        'ssl_ca_cert': 'abcxyz',
                        'project_name': sentinel.prj_name,
                        'type': 'kubernetes',
                        'extra': extra_param}
        vim = {}
        auth_cred = config_param.copy()
        auth_cred.pop('project_name')
        auth_cred.pop('type')
        auth_cred.pop('extra')
        expected_vim = {'auth_cred': auth_cred,
                        'vim_project':
                            {'name': sentinel.prj_name},
                        'type': 'kubernetes',
                        'extra': extra_param}
        vim_utils.args2body_vim(config_param.copy(), vim)
        self.assertEqual(expected_vim, vim)

    def test_args2body_kubernetes_vim_oidc_no_username(self):
        config_param = {'oidc_token_url': sentinel.oidc_token_url,
                        'password': sentinel.password,
                        'client_id': sentinel.client_id,
                        'client_secret': sentinel.client_secret,
                        'ssl_ca_cert': "None",
                        'project_name': sentinel.prj_name,
                        'type': 'kubernetes'}
        vim = {}
        self.assertRaises(exceptions.TackerClientException,
                          vim_utils.args2body_vim,
                          config_param, vim)

    def test_args2body_vim_no_project(self):
        config_param = {'username': sentinel.usrname1,
                        'password': sentinel.password1,
                        'user_domain_name': sentinel.user_domain.name,
                        'cert_verify': 'True',
                        'type': 'openstack'}
        vim = {}
        self.assertRaises(exceptions.TackerClientException,
                          vim_utils.args2body_vim,
                          config_param, vim)

    def test_validate_auth_url_with_port(self):
        auth_url = "http://localhost:8000/test"
        url_parts = vim_utils.validate_auth_url(auth_url)
        self.assertEqual('http', url_parts.scheme)
        self.assertEqual('localhost:8000', url_parts.netloc)
        self.assertEqual(8000, url_parts.port)

    def test_validate_auth_url_without_port(self):
        auth_url = "http://localhost/test"
        url_parts = vim_utils.validate_auth_url(auth_url)
        self.assertEqual('http', url_parts.scheme)
        self.assertEqual('localhost', url_parts.netloc)

    def test_validate_auth_url_exception(self):
        auth_url = "localhost/test"
        self.assertRaises(exceptions.TackerClientException,
                          vim_utils.validate_auth_url,
                          auth_url)
