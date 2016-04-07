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

from oslo_utils import strutils
import yaml

from tackerclient.common import exceptions
from tackerclient.common import utils
from tackerclient.tacker import v1_0 as tackerV10
from tackerclient.tacker.v1_0.nfvo import vim_utils

_VIM = "vim"


class ListVIM(tackerV10.ListCommand):
    """List VIMs that belong to a given tenant."""

    resource = _VIM
    list_columns = ['id', 'tenant_id', 'name', 'type', 'description',
                    'auth_url', 'placement_attr', 'auth_cred']

    def extend_list(self, data, parsed_args):
        for index, value in enumerate(data):
            data[index] = strutils.mask_dict_password(value)


class ShowVIM(tackerV10.ShowCommand):
    """Show information of a given VIM."""

    resource = _VIM


class CreateVIM(tackerV10.CreateCommand):
    """Create a VIM."""

    resource = _VIM

    def add_known_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--config-file', help='specify VIM specific '
                                                 'config parameters in a file')
        group.add_argument('--config', help='specify VIM config parameters '
                                            'as a direct input')
        parser.add_argument(
            '--name',
            help='Set a name for the vim')
        parser.add_argument(
            '--description',
            help='Set a description for the vim')

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        if parsed_args.config_file:
            with open(parsed_args.config_file) as f:
                vim_config = f.read()
                config_param = yaml.load(vim_config)
        if parsed_args.config:
            parsed_args.config = parsed_args.config.decode('unicode_escape')
            config_param = yaml.load(parsed_args.config)
        vim_obj = body[self.resource]
        try:
            auth_url = config_param.pop('auth_url')
        except KeyError:
            raise exceptions.TackerClientException(message='Auth URL must be '
                                                           'specified',
                                                   status_code=404)
        vim_obj['auth_url'] = utils.validate_url(auth_url).geturl()
        vim_obj['type'] = config_param.pop('type', 'openstack')
        vim_utils.args2body_vim(config_param, vim_obj)
        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'description'])
        return body


class UpdateVIM(tackerV10.UpdateCommand):
    """Update a given VIM."""

    resource = _VIM

    def add_known_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '--config-file',
            help='specify VIM specific config parameters in a file')
        group.add_argument(
            '--config',
            help='specify VIM config parameters as a direct input')

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        # config arg passed as data overrides config yaml when both args passed
        if parsed_args.config_file:
            with open(parsed_args.config_file) as f:
                config_yaml = f.read()
            config_param = yaml.load(config_yaml)
        if parsed_args.config:
            parsed_args.config = parsed_args.config.decode('unicode_escape')
            config_param = yaml.load(parsed_args.config)
        if 'auth_url' in config_param:
            raise exceptions.TackerClientException(message='Auth URL cannot '
                                                           'be updated',
                                                   status_code=404)
        vim_obj = body[self.resource]
        vim_utils.args2body_vim(config_param, vim_obj)
        tackerV10.update_dict(parsed_args, body[self.resource], ['tenant_id'])
        return body


class DeleteVIM(tackerV10.DeleteCommand):
    """Delete a given VIM."""
    resource = _VIM
