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


class ListResourceEvents(tackerV10.ListCommand):
    """List events that belong to a given resource.

    The supported args are --id, --resource_id, --resource_state,
    --resource_type, --event_type
    """

    resource = _EVENT
    list_columns = ['id', 'resource_type', 'resource_id',
                    'resource_state', 'event_type',
                    'timestamp', 'event_details']


class ListVNFEvents(ListResourceEvents):
    """List events that belong to a given VNF.

    The supported args are --id, --resource_id, --resource_state, --event_type
    """

    resource = "vnf_event"


class ListVNFDEvents(ListResourceEvents):
    """List events that belong to a given VNFD.

    The supported args are --id, --resource_id, --resource_state, --event_type
    """

    resource = "vnfd_event"


class ListVIMEvents(ListResourceEvents):
    """List events that belong to a given VIM.

    The supported args are --id, --resource_id, --resource_state, --event_type
    """

    resource = "vim_event"


class ShowEvent(tackerV10.ShowCommand):
    """Show event given the event id."""

    resource = _EVENT
