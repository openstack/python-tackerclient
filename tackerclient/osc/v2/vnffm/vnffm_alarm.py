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

from tackerclient.i18n import _
from tackerclient.osc import sdk_utils
from tackerclient.osc import utils as tacker_osc_utils

LOG = logging.getLogger(__name__)

_ATTR_MAP = (
    ('id', 'ID', tacker_osc_utils.LIST_BOTH),
    ('managedObjectId', 'Managed Object Id', tacker_osc_utils.LIST_BOTH),
    ('ackState', 'Ack State', tacker_osc_utils.LIST_BOTH),
    ('eventType', 'Event Type', tacker_osc_utils.LIST_BOTH),
    ('perceivedSeverity', 'Perceived Severity', tacker_osc_utils.LIST_BOTH),
    ('probableCause', 'Probable Cause', tacker_osc_utils.LIST_BOTH)
)

_FORMATTERS = {
    'vnfcInstanceIds': tacker_osc_utils.FormatComplexDataColumn,
    'rootCauseFaultyResource': tacker_osc_utils.FormatComplexDataColumn,
    'correlatedAlarmIds': tacker_osc_utils.FormatComplexDataColumn,
    'faultDetails': tacker_osc_utils.FormatComplexDataColumn,
    '_links': tacker_osc_utils.FormatComplexDataColumn
}

_MIXED_CASE_FIELDS = (
    'managedObjectId', 'rootCauseFaultyResource', 'vnfcInstanceIds',
    'alarmRaisedTime', 'alarmChangedTime', 'alarmClearedTime',
    'alarmAcknowledgedTime', 'ackState', 'perceivedSeverity', 'eventTime',
    'eventType', 'faultType', 'probableCause', 'isRootCause',
    'correlatedAlarmIds', 'faultDetails'
)

_VNF_FM_ALARM_ID = 'vnf_fm_alarm_id'


def _get_columns(vnffm_alarm_obj, action=None):
    if action == 'update':
        column_map = {
            'ackState': 'Ack State'
        }
    else:
        column_map = {
            'id': 'ID',
            'managedObjectId': 'Managed Object Id',
            'ackState': 'Ack State',
            'perceivedSeverity': 'Perceived Severity',
            'eventType': 'Event Type',
            'probableCause': 'Probable Cause'
        }

    if action == 'show':
        column_map.update({
            'vnfcInstanceIds': 'Vnfc Instance Ids',
            'rootCauseFaultyResource': 'Root Cause Faulty Resource',
            'alarmRaisedTime': 'Alarm Raised Time',
            'alarmChangedTime': 'Alarm Changed Time',
            'alarmClearedTime': 'Alarm Cleared Time',
            'alarmAcknowledgedTime': 'Alarm Acknowledged Time',
            'eventTime': 'Event Time',
            'faultType': 'Fault Type',
            'isRootCause': 'Is Root Cause',
            'correlatedAlarmIds': 'Correlated Alarm Ids',
            'faultDetails': 'Fault Details',
            '_links': 'Links'
        })

    return sdk_utils.get_osc_show_columns_for_sdk_resource(
        vnffm_alarm_obj, column_map)


class ListVnfFmAlarm(command.Lister):
    _description = _("List VNF FM alarms")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(ListVnfFmAlarm, self).get_parser(prog_name)
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
        data = client.list_vnf_fm_alarms(**_params)
        headers, columns = tacker_osc_utils.get_column_definitions(
            _ATTR_MAP, long_listing=True)
        return (headers,
                (utils.get_dict_properties(
                    s, columns, formatters=_FORMATTERS,
                    mixed_case_fields=_MIXED_CASE_FIELDS,
                ) for s in data['vnf_fm_alarms']))


class ShowVnfFmAlarm(command.ShowOne):
    _description = _("Display VNF FM alarm details")

    def get_parser(self, prog_name):
        parser = super(ShowVnfFmAlarm, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_FM_ALARM_ID,
            metavar="<vnf-fm-alarm-id>",
            help=_("VNF FM alarm ID to display"))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj = client.show_vnf_fm_alarm(parsed_args.vnf_fm_alarm_id)
        display_columns, columns = _get_columns(obj, action='show')
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj), columns,
            mixed_case_fields=_MIXED_CASE_FIELDS,
            formatters=_FORMATTERS)
        return (display_columns, data)


class UpdateVnfFmAlarm(command.ShowOne):
    _description = _("Update information about an individual VNF FM alarm")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(UpdateVnfFmAlarm, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_FM_ALARM_ID,
            metavar="<vnf-fm-alarm-id>",
            help=_("VNF FM alarm ID to update.")
        )
        update_require_parameters = parser.add_argument_group(
            "require arguments"
        )
        update_require_parameters.add_argument(
            "--ack-state",
            metavar="<ack-state>",
            choices=['ACKNOWLEDGED', 'UNACKNOWLEDGED'],
            help=_("Ask state can be 'ACKNOWLEDGED' or 'UNACKNOWLEDGED'."))
        return parser

    def args2body(self, parsed_args):
        body = {'ackState': parsed_args.ack_state}
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        updated_values = client.update_vnf_fm_alarm(
            parsed_args.vnf_fm_alarm_id, self.args2body(parsed_args))
        display_columns, columns = _get_columns(
            updated_values, action='update')
        data = utils.get_item_properties(
            sdk_utils.DictModel(updated_values), columns,
            mixed_case_fields=_MIXED_CASE_FIELDS,
            formatters=_FORMATTERS)
        return (display_columns, data)
