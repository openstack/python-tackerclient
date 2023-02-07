# Copyright (C) 2023 Fujitsu
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
    ('objectType', 'Object Type', tacker_osc_utils.LIST_BOTH),
    ('_links', 'Links', tacker_osc_utils.LIST_BOTH)
)

_FORMATTERS = {
    'subObjectInstanceIds': tacker_osc_utils.FormatComplexDataColumn,
    'criteria': tacker_osc_utils.FormatComplexDataColumn,
    '_links': tacker_osc_utils.FormatComplexDataColumn
}

_MIXED_CASE_FIELDS = (
    'objectType', 'objectInstanceId', 'subObjectInstanceIds', 'callbackUri'
)

_MIXED_CASE_FIELDS_UPDATE = (
    'callbackUri'
)

_VNF_PM_THRESHOLD_ID = 'vnf_pm_threshold_id'


def _get_columns(vnf_pm_threshold, action=None):
    if action == 'update':
        column_map = {
            'callbackUri': 'Callback Uri'
        }
    else:
        column_map = {
            'id': 'ID',
            'objectType': 'Object Type',
            'objectInstanceId': 'Object Instance Id',
            'subObjectInstanceIds': 'Sub Object Instance Ids',
            'criteria': 'Criteria',
            'callbackUri': 'Callback Uri',
            '_links': 'Links'
        }
    return sdk_utils.get_osc_show_columns_for_sdk_resource(
        vnf_pm_threshold, column_map)


class CreateVnfPmThreshold(command.ShowOne):
    _description = _("Create a new VNF PM threshold")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(CreateVnfPmThreshold, self).get_parser(prog_name)
        parser.add_argument(
            'request_file',
            metavar="<param-file>",
            help=_('Specify create VNF PM threshold request '
                   'parameters in a json file.'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vnf_pm_threshold = client.create_vnf_pm_threshold(
            tacker_osc_utils.jsonfile2body(parsed_args.request_file))
        display_columns, columns = _get_columns(vnf_pm_threshold)
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnf_pm_threshold), columns,
            formatters=_FORMATTERS, mixed_case_fields=_MIXED_CASE_FIELDS)
        return (display_columns, data)


class ListVnfPmThreshold(command.Lister):
    _description = _("List VNF PM thresholds")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(ListVnfPmThreshold, self).get_parser(prog_name)
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
        data = client.list_vnf_pm_thresholds(**_params)
        headers, columns = tacker_osc_utils.get_column_definitions(
            _ATTR_MAP, long_listing=True)
        return (headers,
                (utils.get_dict_properties(
                    s, columns, formatters=_FORMATTERS,
                    mixed_case_fields=_MIXED_CASE_FIELDS,
                ) for s in data['vnf_pm_thresholds']))


class ShowVnfPmThreshold(command.ShowOne):
    _description = _("Display VNF PM threshold details")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(ShowVnfPmThreshold, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_PM_THRESHOLD_ID,
            metavar="<vnf-pm-threshold-id>",
            help=_("VNF PM threshold ID to display"))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj = client.show_vnf_pm_threshold(parsed_args.vnf_pm_threshold_id)
        display_columns, columns = _get_columns(obj)
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj), columns,
            mixed_case_fields=_MIXED_CASE_FIELDS,
            formatters=_FORMATTERS)
        return (display_columns, data)


class UpdateVnfPmThreshold(command.ShowOne):
    _description = _("Update information about an individual VNF PM threshold")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(UpdateVnfPmThreshold, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_PM_THRESHOLD_ID,
            metavar="<vnf-pm-threshold-id>",
            help=_("VNF PM threshold ID to update.")
        )
        parser.add_argument(
            'request_file',
            metavar="<param-file>",
            help=_('Specify update PM threshold request '
                   'parameters in a json file.'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        updated_values = client.update_vnf_pm_threshold(
            parsed_args.vnf_pm_threshold_id,
            tacker_osc_utils.jsonfile2body(parsed_args.request_file))
        display_columns, columns = _get_columns(updated_values, 'update')
        data = utils.get_item_properties(
            sdk_utils.DictModel(updated_values), columns,
            mixed_case_fields=_MIXED_CASE_FIELDS_UPDATE)
        return (display_columns, data)


class DeleteVnfPmThreshold(command.Command):
    _description = _("Delete VNF PM threshold")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(DeleteVnfPmThreshold, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_PM_THRESHOLD_ID,
            metavar="<vnf-pm-threshold-id>",
            nargs="+",
            help=_("VNF PM threshold ID(s) to delete"))
        return parser

    def take_action(self, parsed_args):
        error_count = 0
        client = self.app.client_manager.tackerclient
        vnf_pm_threshold_ids = parsed_args.vnf_pm_threshold_id

        for threshold_id in vnf_pm_threshold_ids:
            try:
                client.delete_vnf_pm_threshold(threshold_id)
            except Exception as e:
                error_count += 1
                LOG.error(_("Failed to delete VNF PM threshold with "
                            "ID '%(threshold_id)s': %(e)s"),
                          {'threshold_id': threshold_id, 'e': e})

        total = len(vnf_pm_threshold_ids)
        if error_count > 0:
            msg = (_("Failed to delete %(error_count)s of %(total)s "
                     "VNF PM thresholds.") %
                   {'error_count': error_count, 'total': total})
            raise exceptions.CommandError(message=msg)

        if total > 1:
            print(_('All specified VNF PM thresholds are deleted '
                    'successfully'))
            return
        print(_("VNF PM threshold '%s' deleted "
                "successfully") % vnf_pm_threshold_ids[0])
