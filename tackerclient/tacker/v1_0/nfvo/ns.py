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

import yaml

from tackerclient.common import exceptions
from tackerclient.i18n import _
from tackerclient.tacker import v1_0 as tackerV10


_NS = 'ns'
_RESOURCE = 'resource'


class ListNS(tackerV10.ListCommand):
    """List NS that belong to a given tenant."""

    resource = _NS
    list_columns = ['id', 'name', 'nsd_id', 'vnf_ids', 'vnffg_ids',
                    'mgmt_ip_addresses', 'status']


class ShowNS(tackerV10.ShowCommand):
    """Show information of a given NS."""

    resource = _NS


class CreateNS(tackerV10.CreateCommand):
    """Create a NS."""

    resource = _NS
    remove_output_fields = ["attributes"]

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Set a name for the NS'))
        parser.add_argument(
            '--description',
            help=_('Set description for the NS'))
        nsd_group = parser.add_mutually_exclusive_group(required=True)
        nsd_group.add_argument(
            '--nsd-id',
            help=_('NSD ID to use as template to create NS'))
        nsd_group.add_argument(
            '--nsd-template',
            help=_('NSD file to create NS'))
        nsd_group.add_argument(
            '--nsd-name',
            help=_('NSD name to use as template to create NS'))
        vim_group = parser.add_mutually_exclusive_group()
        vim_group.add_argument(
            '--vim-id',
            help=_('VIM ID to use to create NS on the specified VIM'))
        vim_group.add_argument(
            '--vim-name',
            help=_('VIM name to use to create NS on the specified VIM'))
        parser.add_argument(
            '--vim-region-name',
            help=_('VIM Region to use to create NS on the specified VIM'))
        parser.add_argument(
            '--param-file',
            help=_('Specify parameter yaml file'))

    def args2body(self, parsed_args):
        args = {'attributes': {}}
        body = {self.resource: args}
        if parsed_args.vim_region_name:
            args.setdefault('placement_attr', {})['region_name'] = \
                parsed_args.vim_region_name

        tacker_client = self.get_client()
        tacker_client.format = parsed_args.request_format
        if parsed_args.vim_name:
            _id = tackerV10.find_resourceid_by_name_or_id(tacker_client,
                                                          'vim',
                                                          parsed_args.
                                                          vim_name)
            parsed_args.vim_id = _id
        if parsed_args.nsd_name:
            _id = tackerV10.find_resourceid_by_name_or_id(tacker_client,
                                                          'nsd',
                                                          parsed_args.
                                                          nsd_name)
            parsed_args.nsd_id = _id
        elif parsed_args.nsd_template:
            with open(parsed_args.nsd_template) as f:
                template = f.read()
            try:
                args['nsd_template'] = yaml.load(
                    template, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(reason=e)
            if not args['nsd_template']:
                raise exceptions.InvalidInput(reason='The nsd file is empty')

        if parsed_args.param_file:
            with open(parsed_args.param_file) as f:
                param_yaml = f.read()
            try:
                args['attributes']['param_values'] = yaml.load(
                    param_yaml, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(reason=e)
        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'description',
                               'nsd_id', 'vim_id'])
        return body


class DeleteNS(tackerV10.DeleteCommand):
    """Delete given NS(s)."""

    resource = _NS
    deleted_msg = {'ns': 'delete initiated'}

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--force',
            default=False,
            action='store_true',
            help=_('Force delete Network Service'))

    def args2body(self, parsed_args):
        if parsed_args.force:
            body = {self.resource: {'attributes': {'force': True}}}
        else:
            body = dict()
        return body
