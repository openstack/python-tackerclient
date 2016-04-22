#
# Copyright 2013 Intel
# Copyright 2013 Isaku Yamahata <isaku.yamahata at intel com>
#                               <isaku.yamahata at gmail com>
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

from tackerclient.tacker import v1_0 as tackerV10


_VNF = 'vnf'


class ListVNF(tackerV10.ListCommand):
    """List device that belong to a given tenant."""

    resource = _VNF
    list_columns = ['id', 'name', 'description', 'mgmt_url', 'status',
                    'vim_id', 'placement_attr']


class ShowVNF(tackerV10.ShowCommand):
    """show information of a given VNF."""

    resource = _VNF


class CreateVNF(tackerV10.CreateCommand):
    """create a VNF."""

    resource = _VNF
    remove_output_fields = ["attributes"]

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name',
            help='Set a name for the vnf')
        vnfd_group = parser.add_mutually_exclusive_group(required=True)
        vnfd_group.add_argument(
            '--vnfd-id',
            help='VNFD ID to use as template to create VNF')
        vnfd_group.add_argument(
            '--vnfd-name',
            help='VNFD Name to use as template to create VNF')
        vim_group = parser.add_mutually_exclusive_group()
        vim_group.add_argument(
            '--vim-id',
            help='VIM ID to use to create VNF on the specified VIM')
        vim_group.add_argument(
            '--vim-name',
            help='VIM name to use to create VNF on the specified VIM')
        parser.add_argument(
            '--vim-region-name',
            help='VIM Region to use to create VNF on the specified VIM')
        parser.add_argument(
            '--config-file',
            help='specify config yaml file')
        parser.add_argument(
            '--config',
            help='specify config yaml data')
        parser.add_argument(
            '--param-file',
            help='specify parameter yaml file'
        )

    def args2body(self, parsed_args):
        args = {'attributes': {}}
        body = {self.resource: args}
        # config arg passed as data overrides config yaml when both args passed
        if parsed_args.config_file:
            with open(parsed_args.config_file) as f:
                config_yaml = f.read()
            args['attributes']['config'] = config_yaml
        if parsed_args.config:
            parsed_args.config = parsed_args.config.decode('unicode_escape')
            args['attributes']['config'] = parsed_args.config

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
        if parsed_args.vnfd_name:
                _id = tackerV10.find_resourceid_by_name_or_id(tacker_client,
                                                              'vnfd',
                                                              parsed_args.
                                                              vnfd_name)
                parsed_args.vnfd_id = _id
        if parsed_args.param_file:
            with open(parsed_args.param_file) as f:
                param_yaml = f.read()
            args['attributes']['param_values'] = param_yaml
        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'vnfd_id', 'vim_id'])
        return body


class UpdateVNF(tackerV10.UpdateCommand):
    """Update a given VNF."""

    resource = _VNF

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--config-file',
            help='specify config yaml file')
        parser.add_argument(
            '--config',
            help='specify config yaml data')

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        # config arg passed as data overrides config yaml when both args passed
        if parsed_args.config_file:
            with open(parsed_args.config_file) as f:
                config_yaml = f.read()
            body[self.resource]['attributes'] = {'config': config_yaml}
        if parsed_args.config:
            parsed_args.config = parsed_args.config.decode('unicode_escape')
            body[self.resource]['attributes'] = {'config': parsed_args.config}
        tackerV10.update_dict(parsed_args, body[self.resource], ['tenant_id'])
        return body


class DeleteVNF(tackerV10.DeleteCommand):
    """Delete a given VNF."""

    resource = _VNF
