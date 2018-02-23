# Copyright 2018 OpenStack Foundation
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
#

from osc_lib.command import command
from osc_lib import utils

from tackerclient.i18n import _
from tackerclient.osc import sdk_utils
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.tacker import v1_0 as tackerV10

_attr_map = (
    ('id', 'ID', tacker_osc_utils.LIST_BOTH),
    ('resource_type', 'Resource Type', tacker_osc_utils.LIST_BOTH),
    ('resource_id', 'Resource ID', tacker_osc_utils.LIST_BOTH),
    ('resource_state', 'Resource State', tacker_osc_utils.LIST_BOTH),
    ('event_type', 'Event Type', tacker_osc_utils.LIST_BOTH),
    ('timestamp', 'Timestamp', tacker_osc_utils.LIST_BOTH),
    ('event_details', 'Event Details', tacker_osc_utils.LIST_LONG_ONLY),
)

_EVENT = "event"

events_path = '/events'


def _get_columns(item):
    column_map = {}
    return sdk_utils.get_osc_show_columns_for_sdk_resource(item, column_map)


class ShowEvent(command.ShowOne):
    _description = _("Show event given the event id.")

    def get_parser(self, prog_name):
        parser = super(ShowEvent, self).get_parser(prog_name)
        parser.add_argument(
            _EVENT,
            metavar="ID",
            help=_("ID of event to display")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _EVENT, parsed_args.event)
        obj = client.show_event(obj_id)
        display_columns, columns = _get_columns(obj[_EVENT])
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj[_EVENT]),
            columns,)
        return (display_columns, data)


class ListEvent(command.Lister):
    _description = _("List events of resources.")

    def get_parser(self, prog_name):
        parser = super(ListEvent, self).get_parser(prog_name)
        parser.add_argument(
            '--id',
            help=_("id of the event to look up."))
        parser.add_argument(
            '--resource-type',
            help=_("resource type of the events to look up."))
        parser.add_argument(
            '--resource-id',
            help=_("resource id of the events to look up."))
        parser.add_argument(
            '--resource-state',
            help=_("resource state of the events to look up."))
        parser.add_argument(
            '--event-type',
            help=_("event type of the events to look up."))
        parser.add_argument(
            '--long',
            action='store_true',
            help=_("List additional fields in output"))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        _params = {}
        if parsed_args.id:
            _params['id'] = parsed_args.id
        if parsed_args.resource_id:
            _params['resource_id'] = parsed_args.resource_id
        if parsed_args.resource_state:
            _params['resource_state'] = parsed_args.resource_id
        if parsed_args.event_type:
            _params['event_type'] = parsed_args.event_type
        if parsed_args.resource_type:
            _params['resource_type'] = parsed_args.resource_type
        events = client.list('events', events_path, True, **_params)
        data = {}
        data['events'] = events['events']
        headers, columns = tacker_osc_utils.get_column_definitions(
            _attr_map, long_listing=parsed_args.long)
        return (headers,
                (utils.get_dict_properties(
                    s, columns,
                ) for s in data[_EVENT + 's']))
