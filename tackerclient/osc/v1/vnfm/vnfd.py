# Copyright 2016 NEC Corporation.
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

_VNFD = "vnfd"

_formatters = {
    'attributes': tacker_osc_utils.format_dict_with_indention,
}


def _get_columns(item):
    column_map = {
        'tenant_id': 'project_id',
    }
    return sdk_utils.get_osc_show_columns_for_sdk_resource(item, column_map)


class CreateVNFD(command.ShowOne):
    _description = _("Create a new VNFD")

    def get_parser(self, prog_name):
        parser = super(CreateVNFD, self).get_parser(prog_name)
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Name for VNFD'))
        parser.add_argument(
            '--tenant-id', metavar='TENANT_ID',
            help=_('The owner tenant ID or project ID'))
        parser.add_argument(
            '--vnfd-file',
            required=True,
            help=_('YAML file with VNFD parameters'))
        parser.add_argument(
            '--description',
            help=_('Set a description for the VNFD'))
        return parser

    def args2body(self, parsed_args):
        body = {_VNFD: {}}
        vnfd = None
        if not parsed_args.vnfd_file:
            raise exceptions.InvalidInput(reason="Invalid input for vnfd file")
        with open(parsed_args.vnfd_file) as f:
            vnfd = f.read()
            try:
                vnfd = yaml.load(vnfd, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                msg = _("yaml failed to load vnfd file. %s") % e
                raise exceptions.InvalidInput(reason=msg)
            if not vnfd:
                raise exceptions.InvalidInput(reason="vnfd file is empty")
            body[_VNFD]['attributes'] = {'vnfd': vnfd}
        tackerV10.update_dict(parsed_args, body[_VNFD],
                              ['tenant_id', 'name', 'description'])
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vnfd = client.create_vnfd(self.args2body(parsed_args))
        display_columns, columns = _get_columns(vnfd[_VNFD])
        vnfd[_VNFD]['attributes']['vnfd'] = yaml.load(
            vnfd[_VNFD]['attributes']['vnfd'])
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnfd[_VNFD]),
            columns, formatters=_formatters)
        return (display_columns, data)


class DeleteVNFD(command.Command):
    _description = _("Delete VNFD(s).")

    def get_parser(self, prog_name):
        parser = super(DeleteVNFD, self).get_parser(prog_name)
        parser.add_argument(
            _VNFD,
            metavar="<VNFD>",
            nargs="+",
            help=_("VNFD(s) to delete (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        failure = False
        deleted_ids = []
        failed_items = {}
        for resource_id in parsed_args.vnfd:
            try:
                obj = tackerV10.find_resourceid_by_name_or_id(
                    client, _VNFD, resource_id)
                client.delete_vnfd(obj)
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
                                                 'resource': _VNFD})
            err_msg = _("\n\nUnable to delete the below"
                        " %s(s):") % _VNFD
            for failed_id, error in failed_items.items():
                err_msg += (_('\n Cannot delete %(failed_id)s: %(error)s')
                            % {'failed_id': failed_id,
                               'error': error})
            msg += err_msg
            raise exceptions.CommandError(message=msg)
        else:
            print((_('All specified %(resource)s(s) deleted successfully')
                   % {'resource': _VNFD}))
        return


class ListVNFD(command.Lister):
    _description = ("List (VNFD)s that belong to a given tenant.")

    def get_parser(self, prog_name):
        parser = super(ListVNFD, self).get_parser(prog_name)
        parser.add_argument(
            '--template-source',
            help=_("List VNFD with specified template source. Available \
                   options are 'onboarded' (default), 'inline' or 'all'"),
            action='store',
            default='onboarded')
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        data = client.list_vnfds()
        headers, columns = tacker_osc_utils.get_column_definitions(
            _attr_map, long_listing=None)
        return (headers,
                (utils.get_dict_properties(
                    s, columns,
                ) for s in data[_VNFD + 's']))


class ShowVNFD(command.ShowOne):
    _description = _("Display VNFD details")

    def get_parser(self, prog_name):
        parser = super(ShowVNFD, self).get_parser(prog_name)
        parser.add_argument(
            _VNFD,
            metavar="<VNFD>",
            help=_("VNFD to display (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _VNFD, parsed_args.vnfd)
        obj = client.show_vnfd(obj_id)
        obj[_VNFD]['attributes']['vnfd'] = yaml.load(
            obj[_VNFD]['attributes']['vnfd'])
        display_columns, columns = _get_columns(obj[_VNFD])
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj[_VNFD]),
            columns,
            formatters=_formatters)
        return (display_columns, data)


class ShowTemplateVNFD(command.ShowOne):
    _description = _("Display VNFD Template details")

    def get_parser(self, prog_name):
        parser = super(ShowTemplateVNFD, self).get_parser(prog_name)
        parser.add_argument(
            _VNFD,
            metavar="<VNFD>",
            help=_("VNFD to display (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _VNFD, parsed_args.vnfd)
        obj = client.show_vnfd(obj_id)
        obj[_VNFD]['attributes']['vnfd'] = yaml.load(
            obj[_VNFD]['attributes']['vnfd'])
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj[_VNFD]),
            (u'attributes',),
            formatters=_formatters)
        data = (data or _('Unable to display VNFD template!'))
        return ((u'attributes',), data)
