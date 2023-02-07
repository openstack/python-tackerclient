# Copyright (C) 2022 Fujitsu
# All Rights Reserved.
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

import logging

from osc_lib.command import command
from osc_lib import utils

from tackerclient.common import exceptions
from tackerclient.i18n import _
from tackerclient.osc import sdk_utils
from tackerclient.osc import utils as tacker_osc_utils

LOG = logging.getLogger(__name__)

_ATTR_MAP = (
    ('id', 'ID', tacker_osc_utils.LIST_BOTH),
    ('callbackUri', 'Callback Uri', tacker_osc_utils.LIST_BOTH)
)

_FORMATTERS = {
    'filter': tacker_osc_utils.FormatComplexDataColumn,
    '_links': tacker_osc_utils.FormatComplexDataColumn
}

_MIXED_CASE_FIELDS = (
    'callbackUri'
)

_VNF_FM_SUB_ID = 'vnf_fm_sub_id'


def _get_columns(vnffm_sub_obj):
    column_map = {
        'id': 'ID',
        'filter': 'Filter',
        'callbackUri': 'Callback Uri',
        '_links': 'Links'
    }

    return sdk_utils.get_osc_show_columns_for_sdk_resource(
        vnffm_sub_obj, column_map)


class CreateVnfFmSub(command.ShowOne):
    _description = _("Create a new VNF FM subscription")

    def get_parser(self, prog_name):
        parser = super(CreateVnfFmSub, self).get_parser(prog_name)
        parser.add_argument(
            'request_file',
            metavar="<param-file>",
            help=_('Specify create VNF FM subscription request '
                   'parameters in a json file.'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vnf_fm_sub = client.create_vnf_fm_sub(
            tacker_osc_utils.jsonfile2body(parsed_args.request_file))
        display_columns, columns = _get_columns(vnf_fm_sub)
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnf_fm_sub), columns,
            formatters=_FORMATTERS, mixed_case_fields=_MIXED_CASE_FIELDS)
        return (display_columns, data)


class ListVnfFmSub(command.Lister):
    _description = _("List VNF FM subs")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(ListVnfFmSub, self).get_parser(prog_name)
        parser.add_argument(
            "--filter",
            metavar="<filter>",
            help=_("Attribute-based-filtering parameters"),
        )
        return parser

    def take_action(self, parsed_args):
        _params = {}
        if parsed_args.filter:
            _params['filter'] = parsed_args.filter

        client = self.app.client_manager.tackerclient
        data = client.list_vnf_fm_subs(**_params)
        headers, columns = tacker_osc_utils.get_column_definitions(
            _ATTR_MAP, long_listing=True)
        return (headers,
                (utils.get_dict_properties(
                    s, columns, formatters=_FORMATTERS,
                    mixed_case_fields=_MIXED_CASE_FIELDS,
                ) for s in data['vnf_fm_subs']))


class ShowVnfFmSub(command.ShowOne):
    _description = _("Display VNF FM subscription details")

    def get_parser(self, prog_name):
        parser = super(ShowVnfFmSub, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_FM_SUB_ID,
            metavar="<vnf-fm-sub-id>",
            help=_("VNF FM subscription ID to display"))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj = client.show_vnf_fm_sub(parsed_args.vnf_fm_sub_id)
        display_columns, columns = _get_columns(obj)
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj), columns,
            mixed_case_fields=_MIXED_CASE_FIELDS,
            formatters=_FORMATTERS)
        return (display_columns, data)


class DeleteVnfFmSub(command.Command):
    _description = _("Delete VNF FM subscription(s)")

    def get_parser(self, prog_name):
        parser = super(DeleteVnfFmSub, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_FM_SUB_ID,
            metavar="<vnf-fm-sub-id>",
            nargs="+",
            help=_("VNF FM subscription ID(s) to delete"))
        return parser

    def take_action(self, parsed_args):
        error_count = 0
        client = self.app.client_manager.tackerclient
        vnf_fm_sub_ids = parsed_args.vnf_fm_sub_id

        for sub_id in vnf_fm_sub_ids:
            try:
                client.delete_vnf_fm_sub(sub_id)
            except Exception as e:
                error_count += 1
                LOG.error(_("Failed to delete VNF FM subscription with "
                            "ID '%(sub_id)s': %(e)s"),
                          {'sub_id': sub_id, 'e': e})

        total = len(vnf_fm_sub_ids)
        if error_count > 0:
            msg = (_("Failed to delete %(error_count)s of %(total)s "
                     "VNF FM subscriptions.") % {'error_count': error_count,
                                                 'total': total})
            raise exceptions.CommandError(message=msg)

        if total > 1:
            print(_('All specified VNF FM subscriptions are deleted '
                    'successfully'))
        else:
            print(_("VNF FM subscription '%s' deleted "
                    "successfully") % vnf_fm_sub_ids[0])
