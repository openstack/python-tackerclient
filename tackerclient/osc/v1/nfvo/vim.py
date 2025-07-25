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

from osc_lib.cli import format_columns
from osc_lib.command import command
from osc_lib import utils
from oslo_utils import strutils

from tackerclient.common import exceptions
from tackerclient.i18n import _
from tackerclient.osc import sdk_utils
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.tacker import v1_0 as tackerV10
from tackerclient.tacker.v1_0.nfvo import vim_utils

_attr_map = (
    ('id', 'ID', tacker_osc_utils.LIST_BOTH),
    ('name', 'Name', tacker_osc_utils.LIST_BOTH),
    ('tenant_id', 'Tenant_id', tacker_osc_utils.LIST_BOTH),
    ('type', 'Type', tacker_osc_utils.LIST_BOTH),
    ('is_default', 'Is Default',
     tacker_osc_utils.LIST_BOTH),
    ('placement_attr', 'Placement attribution',
     tacker_osc_utils.LIST_LONG_ONLY),
    ('status', 'Status', tacker_osc_utils.LIST_BOTH),
)

_VIM = 'vim'


class ListVIM(command.Lister):
    _description = _("List VIMs that belong to a given tenant.")

    def get_parser(self, prog_name):
        parser = super(ListVIM, self).get_parser(prog_name)
        parser.add_argument(
            '--long',
            action='store_true',
            help=_("List additional fields in output")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        data = client.list_vims()
        headers, columns = tacker_osc_utils.get_column_definitions(
            _attr_map, long_listing=parsed_args.long)
        return (headers,
                (utils.get_dict_properties(
                    s, columns,
                ) for s in data[_VIM + 's']))


class ShowVIM(command.ShowOne):
    _description = _("Display VIM details")

    def get_parser(self, prog_name):
        parser = super(ShowVIM, self).get_parser(prog_name)
        parser.add_argument(
            _VIM,
            metavar="<VIM>",
            help=_("VIM to display (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _VIM, parsed_args.vim)
        obj = client.show_vim(obj_id)
        display_columns, columns = _get_columns(obj[_VIM])
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj[_VIM]),
            columns,
            formatters=_formatters)
        return (display_columns, data)


class CreateVIM(command.ShowOne):
    _description = _("Register a new VIM")

    def get_parser(self, prog_name):
        parser = super(CreateVIM, self).get_parser(prog_name)
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Set a name for the VIM'))
        parser.add_argument(
            '--tenant-id', metavar='TENANT_ID',
            help=_('The owner tenant ID or project ID'))
        parser.add_argument(
            '--config-file',
            required=True,
            help=_('YAML file with VIM configuration parameters'))
        parser.add_argument(
            '--description',
            help=_('Set a description for the VIM'))
        parser.add_argument(
            '--is-default',
            action='store_true',
            default=False,
            help=_('Set as default VIM'))
        return parser

    def args2body(self, parsed_args):
        body = {_VIM: {}}
        if parsed_args.config_file:
            with open(parsed_args.config_file) as f:
                vim_config = f.read()
                try:
                    config_param = yaml.load(vim_config,
                                             Loader=yaml.SafeLoader)
                except yaml.YAMLError as e:
                    raise exceptions.InvalidInput(reason=e)
        vim_obj = body[_VIM]
        try:
            auth_url = config_param.pop('auth_url')
        except KeyError:
            raise exceptions.TackerClientException(message='Auth URL must be '
                                                           'specified',
                                                   status_code=404)
        vim_obj['auth_url'] = vim_utils.validate_auth_url(auth_url).geturl()
        vim_utils.args2body_vim(config_param, vim_obj)
        tackerV10.update_dict(parsed_args, body[_VIM],
                              ['tenant_id', 'name', 'description',
                               'is_default'])
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vim = client.create_vim(self.args2body(parsed_args))
        display_columns, columns = _get_columns(vim[_VIM])
        data = utils.get_item_properties(
            sdk_utils.DictModel(vim[_VIM]),
            columns, formatters=_formatters)
        return (display_columns, data)


class DeleteVIM(command.Command):
    _description = _("Delete VIM(s).")

    def get_parser(self, prog_name):
        parser = super(DeleteVIM, self).get_parser(prog_name)
        parser.add_argument(
            _VIM,
            metavar="<VIM>",
            nargs="+",
            help=_("VIM(s) to delete (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        failure = False
        deleted_ids = []
        failed_items = {}
        for resource_id in parsed_args.vim:
            try:
                obj = tackerV10.find_resourceid_by_name_or_id(
                    client, _VIM, resource_id)
                client.delete_vim(obj)
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
                                                 'resource': _VIM})
            err_msg = _("\n\nUnable to delete the below"
                        " %s(s):") % _VIM
            for failed_id, error in failed_items.items():
                err_msg += (_('\n Cannot delete %(failed_id)s: %(error)s')
                            % {'failed_id': failed_id,
                               'error': error})
            msg += err_msg
            raise exceptions.CommandError(message=msg)
        else:
            print((_('All specified %(resource)s(s) deleted successfully')
                   % {'resource': _VIM}))
        return


class UpdateVIM(command.ShowOne):
    _description = _("Update VIM.")

    def get_parser(self, prog_name):
        parser = super(UpdateVIM, self).get_parser(prog_name)
        parser.add_argument(
            'id', metavar="VIM",
            help=_('ID or name of %s to update') % _VIM)
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
        return parser

    def args2body(self, parsed_args):
        body = {_VIM: {}}
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
        vim_obj = body[_VIM]
        if config_param is not None:
            vim_utils.args2body_vim(config_param, vim_obj)
        tackerV10.update_dict(parsed_args, body[_VIM],
                              ['tenant_id', 'name', 'description',
                               'is_default'])
        # type attribute is read-only, it can't be updated, so remove it
        # in update method
        body[_VIM].pop('type', None)
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _VIM, parsed_args.id)
        vim = client.update_vim(obj_id, self.args2body(parsed_args))
        display_columns, columns = _get_columns(vim[_VIM])
        data = utils.get_item_properties(
            sdk_utils.DictModel(vim[_VIM]), columns,
            formatters=_formatters)
        return (display_columns, data)


_formatters = {
    'auth_cred': format_columns.DictColumn,
    'placement_attr': format_columns.DictColumn,
    'vim_project': format_columns.DictColumn,
}


def _get_columns(item):
    column_map = {
        'tenant_id': 'project_id',
    }
    return sdk_utils.get_osc_show_columns_for_sdk_resource(item, column_map)
