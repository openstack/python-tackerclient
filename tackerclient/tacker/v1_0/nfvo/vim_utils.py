# Copyright 2016 Brocade Communications Systems Inc
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


from tackerclient.common import exceptions


def args2body_vim(config_param, vim):
    """Create additional args to vim body

    :param vim: vim request object
    :return: vim body with args populated
    """
    vim['vim_project'] = {'id': config_param.pop('project_id', ''),
                          'name': config_param.pop('project_name', '')}
    if not vim['vim_project']['id'] and not vim['vim_project']['name']:
        raise exceptions.TackerClientException(message='Project Id or name '
                                                       'must be specified',
                                               status_code=404)
    vim['auth_cred'] = {'username': config_param.pop('username', ''),
                        'password': config_param.pop('password', ''),
                        'user_id': config_param.pop('user_id', '')}
