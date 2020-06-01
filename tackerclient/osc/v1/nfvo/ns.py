# Copyright 2018 OpenStack Foundation.
# All Rights Reserved
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
#

import yaml

from osc_lib.command import command
from osc_lib import utils

from tackerclient.common import exceptions
from tackerclient.i18n import _
from tackerclient.osc import sdk_utils
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.tacker import v1_0 as tackerV10

_attr_map = (
    ('id', 'ID', tacker_osc_utils.LIST_BOTH),
    ('name', 'Name', tacker_osc_utils.LIST_BOTH),
    ('nsd_id', 'NSD ID', tacker_osc_utils.LIST_BOTH),
    ('vnf_ids', 'VNF IDs', tacker_osc_utils.LIST_BOTH),
    ('vnffg_ids', 'VNFFG IDs', tacker_osc_utils.LIST_BOTH),
    ('mgmt_ip_addresses', 'Mgmt Ip Addresses', tacker_osc_utils.LIST_BOTH),
    ('status', 'Status', tacker_osc_utils.LIST_BOTH),
)

_NS = 'ns'
_RESOURCE = 'resource'


def _get_columns(item):
    column_map = {
        'tenant_id': 'project_id',
    }
    return sdk_utils.get_osc_show_columns_for_sdk_resource(item, column_map)


class CreateNS(command.ShowOne):
    _description = _("Create a new NS")

    def get_parser(self, prog_name):
        parser = super(CreateNS, self).get_parser(prog_name)
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Name for NS'))
        parser.add_argument(
            '--tenant-id', metavar='TENANT_ID',
            help=_('The owner tenant ID'))
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
            help=_('Specify parameter YAML file'))
        return parser

    def args2body(self, parsed_args):
        body = {_NS: {}}
        body[_NS]['attributes'] = {}

        if parsed_args.vim_region_name:
            body[_NS].setdefault('placement_attr', {})['region_name'] = \
                parsed_args.vim_region_name

        client = self.app.client_manager.tackerclient
        if parsed_args.vim_name:
            _id = tackerV10.find_resourceid_by_name_or_id(client, 'vim',
                                                          parsed_args.vim_name)
            parsed_args.vim_id = _id
        if parsed_args.nsd_name:
            _id = tackerV10.find_resourceid_by_name_or_id(client, 'nsd',
                                                          parsed_args.nsd_name)
            parsed_args.nsd_id = _id
        elif parsed_args.nsd_template:
            with open(parsed_args.nsd_template) as f:
                template = f.read()
                try:
                    template = yaml.load(
                        template, Loader=yaml.SafeLoader)
                except yaml.YAMLError as e:
                    raise exceptions.InvalidInput(reason=e)
                if not template:
                    raise exceptions.InvalidInput(
                        reason='The nsd file is empty')
                body[_NS]['nsd_template'] = template

        if parsed_args.param_file:
            with open(parsed_args.param_file) as f:
                param_yaml = f.read()
            try:
                param_yaml = yaml.load(
                    param_yaml, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(reason=e)
            if not param_yaml:
                raise exceptions.InvalidInput(
                    reason='The parameter file is empty')
            body[_NS]['attributes'] = {'param_values': param_yaml}
        tackerV10.update_dict(parsed_args, body[_NS],
                              ['tenant_id', 'name', 'description',
                               'nsd_id', 'vim_id'])
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        ns = client.create_ns(self.args2body(parsed_args))
        display_columns, columns = _get_columns(ns[_NS])
        data = utils.get_item_properties(
            sdk_utils.DictModel(ns[_NS]),
            columns)
        lstdata = list(data)
        for index, value in enumerate(lstdata):
            if value is None:
                lstdata[index] = ''
        data = tuple(lstdata)
        return (display_columns, data)


class DeleteNS(command.Command):
    _description = _("Delete NS(s).")

    def get_parser(self, prog_name):
        parser = super(DeleteNS, self).get_parser(prog_name)
        parser.add_argument(
            _NS,
            metavar="<NS>",
            nargs="+",
            help=_("NS(s) to delete (name or ID)")
        )
        parser.add_argument(
            '--force',
            default=False,
            action='store_true',
            help=_('Force delete Network Service')
        )
        return parser

    def args2body(self, parsed_args):
        if parsed_args.force:
            body = {_NS: {'attributes': {'force': True}}}
        else:
            body = dict()
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        failure = False
        deleted_ids = []
        failed_items = {}
        body = self.args2body(parsed_args)
        for resource_id in parsed_args.ns:
            try:
                obj = tackerV10.find_resourceid_by_name_or_id(
                    client, _NS, resource_id)
                client.delete_ns(obj, body)
                deleted_ids.append(resource_id)
            except Exception as e:
                failure = True
                failed_items[resource_id] = e
        if failure:
            msg = ''
            if deleted_ids:
                msg = (_('Successfully deleted %(resource)s(s):'
                         ' %(deleted_list)s') % {'deleted_list':
                                                 ', '.join(deleted_ids),
                                                 'resource': _NS})
            err_msg = _("\n\nUnable to delete the below"
                        " %s(s):") % _NS
            for failed_id, error in failed_items.items():
                err_msg += (_('\n Cannot delete %(failed_id)s: %(error)s')
                            % {'failed_id': failed_id,
                               'error': error})
            msg += err_msg
            raise exceptions.CommandError(message=msg)
        else:
            print((_('All specified %(resource)s(s) deleted successfully')
                   % {'resource': _NS}))
        return


class ListNS(command.Lister):
    _description = ("List (NS)s that belong to a given tenant.")

    def get_parser(self, prog_name):
        parser = super(ListNS, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        data = client.list_nss()
        headers, columns = tacker_osc_utils.get_column_definitions(
            _attr_map, long_listing=None)
        return (headers,
                (utils.get_dict_properties(
                    s, columns,
                ) for s in data[_NS + 's']))


class ShowNS(command.ShowOne):
    _description = _("Display NS details")

    def get_parser(self, prog_name):
        parser = super(ShowNS, self).get_parser(prog_name)
        parser.add_argument(
            _NS,
            metavar="<NS>",
            help=_("NS to display (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _NS, parsed_args.ns)
        obj = client.show_ns(obj_id)
        display_columns, columns = _get_columns(obj[_NS])
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj[_NS]),
            columns)
        lstdata = list(data)
        for index, value in enumerate(lstdata):
            if value is None:
                lstdata[index] = ''
        data = tuple(lstdata)
        return (display_columns, data)
