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
from oslo_utils import encodeutils

from tackerclient.common import exceptions
from tackerclient.i18n import _
from tackerclient.osc import sdk_utils
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.tacker import v1_0 as tackerV10

_attr_map = (
    ('id', 'ID', tacker_osc_utils.LIST_BOTH),
    ('name', 'Name', tacker_osc_utils.LIST_BOTH),
    ('mgmt_ip_address', 'Mgmt Ip Address',
     tacker_osc_utils.LIST_BOTH),
    ('status', 'Status', tacker_osc_utils.LIST_BOTH),
    ('vim_id', 'VIM ID', tacker_osc_utils.LIST_BOTH),
    ('vnfd_id', 'VNFD ID', tacker_osc_utils.LIST_BOTH),
    ('tenant_id', 'Project ID', tacker_osc_utils.LIST_LONG_ONLY),
)

_attr_map_rsc = (
    ('id', 'ID', tacker_osc_utils.LIST_BOTH),
    ('name', 'Name', tacker_osc_utils.LIST_BOTH),
    ('type', 'Type', tacker_osc_utils.LIST_BOTH),
)

_VNF = "vnf"


def _get_columns(item):
    column_map = {
        'tenant_id': 'project_id',
    }
    return sdk_utils.get_osc_show_columns_for_sdk_resource(item, column_map)


def _break_string(vnf_monitoring_policy):
    count_space = 0
    monitoring_policy = "\n"
    for i in range(0, len(vnf_monitoring_policy)):
        monitoring_policy += vnf_monitoring_policy[i]
        if vnf_monitoring_policy[i] == ' ':
            count_space += 1
        if count_space == 9:
            monitoring_policy += "\n"
            count_space = 0
    return monitoring_policy


class CreateVNF(command.ShowOne):
    _description = _("Create a new VNF")

    def get_parser(self, prog_name):
        parser = super(CreateVNF, self).get_parser(prog_name)
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Set a name for the VNF'))
        parser.add_argument(
            '--tenant-id', metavar='TENANT_ID',
            help=_('The owner tenant ID or project ID'))
        vnfd_group = parser.add_mutually_exclusive_group(required=True)
        vnfd_group.add_argument(
            '--vnfd-id',
            help=_('VNFD ID to use as template to create VNF'))
        vnfd_group.add_argument(
            '--vnfd-name',
            help=_('VNFD Name to use as template to create VNF'))
        vnfd_group.add_argument(
            '--vnfd-template',
            help=_("VNFD file to create VNF"))
        vim_group = parser.add_mutually_exclusive_group()
        vim_group.add_argument(
            '--vim-id',
            help=_('VIM ID to deploy VNF on specified VIM'))
        vim_group.add_argument(
            '--vim-name',
            help=_('VIM name to deploy VNF on specified VIM'))
        parser.add_argument(
            '--vim-region-name',
            help=_('VIM Region to deploy VNF on specified VIM'))
        parser.add_argument(
            '--config-file',
            help=_('YAML file with VNF configuration'))
        parser.add_argument(
            '--param-file',
            help=_('Specify parameter yaml file'))
        parser.add_argument(
            '--description',
            help=_('Set description for the VNF'))
        return parser

    def args2body(self, parsed_args):
        body = {_VNF: {}}
        body[_VNF]['attributes'] = {}

        config = None
        if parsed_args.config_file:
            with open(parsed_args.config_file) as f:
                config_yaml = f.read()
            try:
                config = yaml.load(
                    config_yaml, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(reason=e)
        if config:
            body[_VNF]['attributes'] = {'config': config}

        if parsed_args.vim_region_name:
            body[_VNF].setdefault('placement_attr', {})['region_name'] = \
                parsed_args.vim_region_name

        client = self.app.client_manager.tackerclient
        if parsed_args.vim_name:
            _id = tackerV10.find_resourceid_by_name_or_id(client, 'vim',
                                                          parsed_args.vim_name)
            parsed_args.vim_id = _id
        if parsed_args.vnfd_name:
            _id = tackerV10.find_resourceid_by_name_or_id(
                client, 'vnfd',
                parsed_args.vnfd_name
            )
            parsed_args.vnfd_id = _id
        elif parsed_args.vnfd_template:
            with open(parsed_args.vnfd_template) as f:
                template = f.read()
                try:
                    template = yaml.load(
                        template, Loader=yaml.SafeLoader)
                except yaml.YAMLError as e:
                    raise exceptions.InvalidInput(reason=e)
                if not template:
                    raise exceptions.InvalidInput(
                        reason='The vnfd file is empty')
                body[_VNF]['vnfd_template'] = template

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
            body[_VNF]['attributes'] = {'param_values': param_yaml}
        tackerV10.update_dict(parsed_args, body[_VNF],
                              ['tenant_id', 'name', 'description',
                               'vnfd_id', 'vim_id'])
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vnf = client.create_vnf(self.args2body(parsed_args))
        display_columns, columns = _get_columns(vnf[_VNF])
        if vnf[_VNF]['attributes'].get('monitoring_policy'):
            vnf[_VNF]['attributes']['monitoring_policy'] =\
                _break_string(vnf[_VNF]['attributes']['monitoring_policy'])
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnf[_VNF]),
            columns)
        return (display_columns, data)


class DeleteVNF(command.Command):
    _description = _("Delete VNF(s).")

    def get_parser(self, prog_name):
        parser = super(DeleteVNF, self).get_parser(prog_name)
        parser.add_argument(
            _VNF,
            metavar="<VNF>",
            nargs="+",
            help=_("VNF(s) to delete (name or ID)"))
        parser.add_argument(
            '--force',
            default=False,
            action='store_true',
            help=_('Force delete VNF instance'))
        return parser

    def args2body(self, parsed_args):
        body = dict()
        if parsed_args.force:
            body[_VNF] = dict()
            body[_VNF]['attributes'] = dict()
            body[_VNF]['attributes']['force'] = True
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        failure = False
        deleted_ids = []
        failed_items = {}
        body = self.args2body(parsed_args)
        for resource_id in parsed_args.vnf:
            try:
                obj = tackerV10.find_resourceid_by_name_or_id(
                    client, _VNF, resource_id)
                client.delete_vnf(obj, body)
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
                                                 'resource': _VNF})
            err_msg = _("\n\nUnable to delete the below"
                        " %s(s):") % _VNF
            for failed_id, error in failed_items.items():
                err_msg += (_('\n Cannot delete %(failed_id)s: %(error)s')
                            % {'failed_id': failed_id,
                               'error': error})
            msg += err_msg
            raise exceptions.CommandError(message=msg)
        else:
            print((_('All specified %(resource)s(s) deleted successfully')
                   % {'resource': _VNF}))
        return


class ListVNF(command.Lister):
    _description = _("List VNF(s) that belong to a given tenant.")

    def get_parser(self, prog_name):
        parser = super(ListVNF, self).get_parser(prog_name)
        parser.add_argument(
            '--template-source',
            help=_("List VNF with specified template source. Available \
                   options are 'onboarded' (default), 'inline' or 'all'"),
            action='store',
            default='onboarded')
        vim_group = parser.add_mutually_exclusive_group()
        vim_group.add_argument(
            '--vim-id',
            help=_('List VNF(s) that belong to a given VIM ID'))
        vim_group.add_argument(
            '--vim-name',
            help=_('List VNF(s) that belong to a given VIM Name'))
        vnfd_group = parser.add_mutually_exclusive_group()
        vnfd_group.add_argument(
            '--vnfd-id',
            help=_('List VNF(s) that belong to a given VNFD ID'))
        vnfd_group.add_argument(
            '--vnfd-name',
            help=_('List VNF(s) that belong to a given VNFD Name'))
        parser.add_argument(
            '--tenant-id', metavar='TENANT_ID',
            help=_('The owner tenant ID or project ID'))
        parser.add_argument(
            '--long',
            action='store_true',
            help=_('List additional fields in output'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        _params = {}
        if parsed_args.vim_id:
            _params['vim_id'] = parsed_args.vim_id
        if parsed_args.vim_name:
            vim_id = tackerV10.find_resourceid_by_name_or_id(
                client, 'vim', parsed_args.vim_name
            )
            _params['vim_id'] = vim_id
        if parsed_args.vnfd_id:
            _params['vnfd_id'] = parsed_args.vnfd_id
        if parsed_args.vnfd_name:
            vim_id = tackerV10.find_resourceid_by_name_or_id(
                client, 'vnfd', parsed_args.vnfd_name
            )
            _params['vnfd_id'] = vim_id
        if parsed_args.tenant_id:
            _params['tenant_id'] = parsed_args.tenant_id
        data = client.list_vnfs(**_params)
        headers, columns = tacker_osc_utils.get_column_definitions(
            _attr_map, long_listing=parsed_args.long)
        return (headers,
                (utils.get_dict_properties(
                    s, columns,
                ) for s in data[_VNF + 's']))


class ShowVNF(command.ShowOne):
    _description = _("Display VNF details")

    def get_parser(self, prog_name):
        parser = super(ShowVNF, self).get_parser(prog_name)
        parser.add_argument(
            _VNF,
            metavar="<VNF>",
            help=_("VNF to display (name or ID)"))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _VNF, parsed_args.vnf)
        obj = client.show_vnf(obj_id)
        if obj[_VNF]['attributes'].get('monitoring_policy'):
            obj[_VNF]['attributes']['monitoring_policy'] =\
                _break_string(obj[_VNF]['attributes']['monitoring_policy'])
        display_columns, columns = _get_columns(obj[_VNF])
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj[_VNF]),
            columns)
        return (display_columns, data)


class ListVNFResources(command.Lister):
    _description = _("List resources of a VNF like VDU, CP, etc.")

    def get_parser(self, prog_name):
        parser = super(ListVNFResources, self).get_parser(prog_name)
        parser.add_argument(
            _VNF,
            metavar="<VNF>",
            help=_("VNF to display (name or ID)"))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _VNF, parsed_args.vnf)
        data = client.list_vnf_resources(obj_id)
        headers, columns = tacker_osc_utils.get_column_definitions(
            _attr_map_rsc, long_listing=None)
        return (headers,
                (utils.get_dict_properties(
                    s, columns,
                ) for s in data['resources']))


class UpdateVNF(command.ShowOne):
    _description = _("Update a given VNF.")

    def get_parser(self, prog_name):
        parser = super(UpdateVNF, self).get_parser(prog_name)
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '--config-file',
            help=_('YAML file with VNF configuration'))
        group.add_argument(
            '--config',
            help=_('YAML data with VNF configuration'))
        group.add_argument(
            '--param-file',
            help=_('YAML file with VNF parameter'))
        parser.add_argument(
            _VNF,
            metavar="<VNF>",
            help=_("VNF to update (name or ID)"))
        return parser

    def args2body(self, parsed_args):
        body = {_VNF: {}}
        body[_VNF]['attributes'] = {}

        config = None
        if parsed_args.config_file:
            with open(parsed_args.config_file) as f:
                config_yaml = f.read()
            try:
                config = yaml.load(config_yaml, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(reason=e)
            if not config:
                raise exceptions.InvalidInput(
                    reason='The config file is empty')
        if parsed_args.config:
            decoded_config = encodeutils.safe_decode(parsed_args.config)
            try:
                config = yaml.load(decoded_config, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(reason=e)
            if not config:
                raise exceptions.InvalidInput(
                    reason='The parameter is empty')
        if config:
            body[_VNF]['attributes'] = {'config': config}
        if parsed_args.param_file:
            with open(parsed_args.param_file) as f:
                param_yaml = f.read()
            try:
                param = yaml.load(
                    param_yaml, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(reason=e)
            if not param:
                raise exceptions.InvalidInput(
                    reason='The parameter file is empty')
            body[_VNF]['attributes'] = {'param_values': param}
        tackerV10.update_dict(parsed_args, body[_VNF], ['tenant_id'])
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _VNF, parsed_args.vnf)
        vnf = client.update_vnf(obj_id, self.args2body(parsed_args))
        if vnf[_VNF]['attributes'].get('monitoring_policy'):
            vnf[_VNF]['attributes']['monitoring_policy'] =\
                _break_string(vnf[_VNF]['attributes']['monitoring_policy'])
        display_columns, columns = _get_columns(vnf[_VNF])
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnf[_VNF]),
            columns)
        return (display_columns, data)


class ScaleVNF(command.Command):
    _description = _("Scale a VNF.")

    def get_parser(self, prog_name):
        parser = super(ScaleVNF, self).get_parser(prog_name)
        parser.add_argument(
            '--scaling-policy-name',
            help=_('VNF policy name used to scale'))
        parser.add_argument(
            '--scaling-type',
            help=_('VNF scaling type, it could be either "out" or "in"'))
        parser.add_argument(
            _VNF,
            metavar="<VNF>",
            help=_("VNF to scale (name or ID)"))
        return parser

    def args2body(self, parsed_args):
        args = {}
        body = {"scale": args}
        args['type'] = parsed_args.scaling_type
        args['policy'] = parsed_args.scaling_policy_name
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _VNF, parsed_args.vnf)
        client.scale_vnf(obj_id, self.args2body(parsed_args))
        return
