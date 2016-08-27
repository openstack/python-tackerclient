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


from mock import sentinel
import testtools

from tackerclient.common import exceptions
from tackerclient.tacker.v1_0.nfvo import vim_utils


class CLITestAuthNoAuth(testtools.TestCase):

    def test_args2body_vim(self):
        config_param = {'project_id': sentinel.prj_id1,
                        'username': sentinel.usrname1,
                        'password': sentinel.password1,
                        'project_domain_name': sentinel.prj_domain_name1,
                        'user_domain_name': sentinel.user_domain.name, }
        vim = {}
        auth_cred = config_param.copy()
        auth_cred.pop('project_id')
        auth_cred.pop('project_domain_name')
        auth_cred.update({'user_id': ''})
        expected_vim = {'auth_cred': auth_cred,
                        'vim_project':
                            {'id': sentinel.prj_id1,
                             'name': '',
                             'project_domain_name': sentinel.prj_domain_name1}}
        vim_utils.args2body_vim(config_param.copy(), vim)
        self.assertEqual(expected_vim, vim)

    def test_args2body_vim_no_project(self):
        config_param = {'username': sentinel.usrname1,
                        'password': sentinel.password1,
                        'user_domain_name': sentinel.user_domain.name, }
        vim = {}
        self.assertRaises(exceptions.TackerClientException,
                          vim_utils.args2body_vim,
                          config_param, vim)
