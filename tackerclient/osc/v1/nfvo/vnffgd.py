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
    ('template_source', 'Template_Source',
     tacker_osc_utils.LIST_BOTH),
    ('description', 'Description', tacker_osc_utils.LIST_BOTH),
)

_VNFFGD = "vnffgd"

_formatters = {
    'template': tacker_osc_utils.format_dict_with_indention,
}


def _get_columns(item):
    column_map = {
        'tenant_id': 'project_id',
    }
    return sdk_utils.get_osc_show_columns_for_sdk_resource(item, column_map)


class CreateVNFFGD(command.ShowOne):
    _description = _("Create a new VNFFGD")

    def get_parser(self, prog_name):
        parser = super(CreateVNFFGD, self).get_parser(prog_name)
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Name for VNFFGD'))
        parser.add_argument(
            '--tenant-id', metavar='TENANT_ID',
            help=_('The owner tenant ID or project ID'))
        parser.add_argument(
            '--vnffgd-file',
            required=True,
            help=_('YAML file with VNFFGD parameters'))
        parser.add_argument(
            '--description',
            help=_('Set a description for the VNFFGD'))
        return parser

    def args2body(self, parsed_args):
        body = {_VNFFGD: {}}
        vnffgd = None
        if not parsed_args.vnffgd_file:
            raise exceptions.InvalidInput(
                reason="Invalid input for vnffgd file")
        with open(parsed_args.vnffgd_file) as f:
            vnffgd = f.read()
            try:
                vnffgd = yaml.load(vnffgd, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(reason=e)
            if not vnffgd:
                raise exceptions.InvalidInput(reason="vnffgd file is empty")
            body[_VNFFGD]['template'] = {'vnffgd': vnffgd}
        tackerV10.update_dict(parsed_args, body[_VNFFGD],
                              ['tenant_id', 'name', 'description'])
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vnffgd = client.create_vnffgd(self.args2body(parsed_args))
        display_columns, columns = _get_columns(vnffgd[_VNFFGD])
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnffgd[_VNFFGD]),
            columns, formatters=_formatters)
        return (display_columns, data)


class DeleteVNFFGD(command.Command):
    _description = _("Delete VNFFGD(s).")

    def get_parser(self, prog_name):
        parser = super(DeleteVNFFGD, self).get_parser(prog_name)
        parser.add_argument(
            _VNFFGD,
            metavar="<VNFFGD>",
            nargs="+",
            help=_("VNFFGD(s) to delete (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        failure = False
        deleted_ids = []
        failed_items = {}
        for resource_id in parsed_args.vnffgd:
            try:
                obj = tackerV10.find_resourceid_by_name_or_id(
                    client, _VNFFGD, resource_id)
                client.delete_vnffgd(obj)
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
                                                 'resource': _VNFFGD})
            err_msg = _("\n\nUnable to delete the below"
                        " %s(s):") % _VNFFGD
            for failed_id, error in failed_items.items():
                err_msg += (_('\n Cannot delete %(failed_id)s: %(error)s')
                            % {'failed_id': failed_id,
                               'error': error})
            msg += err_msg
            raise exceptions.CommandError(message=msg)
        else:
            print((_('All specified %(resource)s(s) deleted successfully')
                   % {'resource': _VNFFGD}))
        return


class ListVNFFGD(command.Lister):
    _description = ("List (VNFFGD)s that belong to a given tenant.")

    def get_parser(self, prog_name):
        parser = super(ListVNFFGD, self).get_parser(prog_name)
        parser.add_argument(
            '--template-source',
            help=_("List VNFFGD with specified template source. Available \
                   options are 'onboarded' (default), 'inline' or 'all'"),
            action='store',
            default='onboarded')
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        data = client.list_vnffgds()
        headers, columns = tacker_osc_utils.get_column_definitions(
            _attr_map, long_listing=None)
        return (headers,
                (utils.get_dict_properties(
                    s, columns,
                ) for s in data[_VNFFGD + 's']))


class ShowVNFFGD(command.ShowOne):
    _description = _("Display VNFFGD details")

    def get_parser(self, prog_name):
        parser = super(ShowVNFFGD, self).get_parser(prog_name)
        parser.add_argument(
            _VNFFGD,
            metavar="<VNFFGD>",
            help=_("VNFFGD to display (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _VNFFGD, parsed_args.vnffgd)
        obj = client.show_vnffgd(obj_id)
        display_columns, columns = _get_columns(obj[_VNFFGD])
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj[_VNFFGD]),
            columns, formatters=_formatters)
        return (display_columns, data)


class ShowTemplateVNFFGD(command.ShowOne):
    _description = _("Display VNFFGD Template details")

    def get_parser(self, prog_name):
        parser = super(ShowTemplateVNFFGD, self).get_parser(prog_name)
        parser.add_argument(
            _VNFFGD,
            metavar="<VNFFGD>",
            help=_("VNFFGD to display (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _VNFFGD, parsed_args.vnffgd)
        obj = client.show_vnffgd(obj_id)
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj[_VNFFGD]),
            (u'template',),
            formatters=_formatters)
        data = (data or _('Unable to display VNFFGD template!'))
        return ((u'template',), data)
