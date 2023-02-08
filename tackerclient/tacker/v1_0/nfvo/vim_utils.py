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

from urllib import parse as urlparse

from tackerclient.common import exceptions


def args2body_vim(config_param, vim):
    """Create additional args to vim body

    :param vim: vim request object
    :return: vim body with args populated
    """
    vim_type = ['openstack', 'kubernetes']
    cert_verify_type = ['True', 'False']

    if 'type' in config_param:
        vim['type'] = config_param.pop('type', '')
        if not vim['type'] in vim_type:
            raise exceptions.TackerClientException(
                message='Supported VIM types: openstack, kubernetes',
                status_code=400)
    else:
        vim['type'] = 'openstack'
    if vim['type'] == 'openstack':
        vim['vim_project'] = {
            'name': config_param.pop('project_name', ''),
            'project_domain_name':
                config_param.pop('project_domain_name', '')}
        if not vim['vim_project']['name']:
            raise exceptions.TackerClientException(
                message='Project name must be specified',
                status_code=404)
        cert_verify = config_param.pop('cert_verify', 'True')
        if cert_verify not in cert_verify_type:
            raise exceptions.TackerClientException(
                message='Supported cert_verify types: True, False',
                status_code=400)
        vim['auth_cred'] = {'username': config_param.pop('username', ''),
                            'password': config_param.pop('password', ''),
                            'user_domain_name':
                                config_param.pop('user_domain_name', ''),
                            'cert_verify': cert_verify}
    elif vim['type'] == 'kubernetes':
        vim['vim_project'] = {
            'name': config_param.pop('project_name', '')}
        if not vim['vim_project']['name']:
            raise exceptions.TackerClientException(
                message='Project name must be specified in Kubernetes VIM,'
                        'it is namespace in Kubernetes environment',
                status_code=404)
        if 'oidc_token_url' in config_param:
            if ('username' not in config_param or
                    'password' not in config_param or
                    'client_id' not in config_param):
                # the username, password, client_id are required.
                # client_secret is not required when client type is public.
                raise exceptions.TackerClientException(
                    message='oidc_token_url must be specified with username,'
                            ' password, client_id, client_secret(optional).',
                    status_code=404)
            vim['auth_cred'] = {
                'oidc_token_url': config_param.pop('oidc_token_url'),
                'username': config_param.pop('username'),
                'password': config_param.pop('password'),
                'client_id': config_param.pop('client_id')}
            if 'client_secret' in config_param:
                vim['auth_cred']['client_secret'] = config_param.pop(
                    'client_secret')
        elif ('username' in config_param) and ('password' in config_param):
            vim['auth_cred'] = {
                'username': config_param.pop('username', ''),
                'password': config_param.pop('password', '')}
        elif 'bearer_token' in config_param:
            vim['auth_cred'] = {
                'bearer_token': config_param.pop('bearer_token', '')}
        else:
            raise exceptions.TackerClientException(
                message='username and password or bearer_token must be'
                        'provided',
                status_code=404)
        ssl_ca_cert = config_param.pop('ssl_ca_cert', '')
        if ssl_ca_cert:
            vim['auth_cred']['ssl_ca_cert'] = ssl_ca_cert
    if 'extra' in config_param:
        vim['extra'] = config_param.pop('extra')


def validate_auth_url(url):
    url_parts = urlparse.urlparse(url)
    if not url_parts.scheme or not url_parts.netloc:
        raise exceptions.TackerClientException(message='Invalid auth URL')
    return url_parts
