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

import yaml

from oslo_utils import strutils

from tackerclient.common import exceptions
from tackerclient.i18n import _
from tackerclient.tacker import v1_0 as tackerV10
from tackerclient.tacker.v1_0.nfvo import vim_utils

_VIM = "vim"


class ListVIM(tackerV10.ListCommand):
    """List VIMs that belong to a given tenant."""

    resource = _VIM
    list_columns = ['id', 'tenant_id', 'name', 'type', 'is_default',
                    'placement_attr', 'status']


class ShowVIM(tackerV10.ShowCommand):
    """Show information of a given VIM."""

    resource = _VIM


class CreateVIM(tackerV10.CreateCommand):
    """Create a VIM."""

    resource = _VIM

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--config-file',
            required=True,
            help=_('YAML file with VIM configuration parameters'))
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Set a name for the VIM'))
        parser.add_argument(
            '--description',
            help=_('Set a description for the VIM'))
        parser.add_argument(
            '--is-default',
            action='store_true',
            default=False,
            help=_('Set as default VIM'))

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        if parsed_args.config_file:
            with open(parsed_args.config_file) as f:
                vim_config = f.read()
                try:
                    config_param = yaml.load(vim_config,
                                             Loader=yaml.SafeLoader)
                except yaml.YAMLError as e:
                    raise exceptions.InvalidInput(reason=e)
        vim_obj = body[self.resource]
        try:
            auth_url = config_param.pop('auth_url')
        except KeyError:
            raise exceptions.TackerClientException(message='Auth URL must be '
                                                           'specified',
                                                   status_code=404)
        vim_obj['auth_url'] = vim_utils.validate_auth_url(auth_url).geturl()
        vim_utils.args2body_vim(config_param, vim_obj)
        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'description',
                               'is_default'])
        return body


class UpdateVIM(tackerV10.UpdateCommand):
    """Update a given VIM."""

    resource = _VIM

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--config-file',
            required=False,
            help=_('YAML file with VIM configuration parameters'))
        parser.add_argument(
            '--name',
            help=_('New name for the VIM'))
        parser.add_argument(
            '--description',
            help=_('New description for the VIM'))
        parser.add_argument(
            '--is-default',
            type=strutils.bool_from_string,
            metavar='{True,False}',
            help=_('Indicate whether the VIM is used as default'))

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        config_param = None
        # config arg passed as data overrides config yaml when both args passed
        if parsed_args.config_file:
            with open(parsed_args.config_file) as f:
                config_yaml = f.read()
            try:
                config_param = yaml.load(config_yaml,
                                         Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(reason=e)
        vim_obj = body[self.resource]
        if config_param is not None:
            vim_utils.args2body_vim(config_param, vim_obj)
        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'description',
                               'is_default'])
        # type attribute is read-only, it can't be updated, so remove it
        # in update method
        body['vim'].pop('type', None)
        return body


class DeleteVIM(tackerV10.DeleteCommand):
    """Delete given VIM(s)."""
    resource = _VIM
