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

from tackerclient.tacker import v1_0 as tackerV10

_EVENT = "event"


class ListEventsBase(tackerV10.ListCommand):
    """Base class for list command."""

    list_columns = ['id', 'resource_type', 'resource_id',
                    'resource_state', 'event_type',
                    'timestamp', 'event_details']

    def get_parser(self, prog_name):
        parser = super(ListEventsBase, self).get_parser(prog_name)
        parser.add_argument('--id',
                            help='id of the event to look up.')
        parser.add_argument('--resource-id',
                            help='resource id of the events to look up.')
        parser.add_argument('--resource-state',
                            help='resource state of the events to look up.')
        parser.add_argument('--event-type',
                            help='event type of the events to look up.')
        return parser

    def args2search_opts(self, parsed_args):
        search_opts = super(ListEventsBase, self).args2search_opts(
            parsed_args)
        if parsed_args.id:
            search_opts.update({'id': parsed_args.id})
        if parsed_args.resource_id:
            search_opts.update({'resource_id': parsed_args.resource_id})
        if parsed_args.resource_state:
            search_opts.update({'resource_state': parsed_args.resource_state})
        if parsed_args.event_type:
            search_opts.update({'event_type': parsed_args.event_type})
        return search_opts


class ListResourceEvents(ListEventsBase):
    """List events of resources."""

    resource = _EVENT

    def get_parser(self, prog_name):
        parser = super(ListResourceEvents, self).get_parser(prog_name)
        parser.add_argument('--resource-type',
                            help='resource type of the events to look up.')
        return parser

    def args2search_opts(self, parsed_args):
        search_opts = super(ListResourceEvents, self).args2search_opts(
            parsed_args)
        if parsed_args.resource_type:
            search_opts.update({'resource_type': parsed_args.resource_type})
        return search_opts


class ListVNFEvents(ListEventsBase):
    """List events of VNFs."""

    resource = "vnf_event"


class ListVNFDEvents(ListEventsBase):
    """List events of VNFDs."""

    resource = "vnfd_event"


class ListVIMEvents(ListEventsBase):
    """List events of VIMs."""

    resource = "vim_event"


class ShowEvent(tackerV10.ShowCommand):
    """Show event given the event id."""

    resource = _EVENT
