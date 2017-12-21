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

from osc_lib.command import command
from osc_lib import utils

from tackerclient.i18n import _
from tackerclient.osc import utils as tacker_osc_utils

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
                ) for s in data['vims']))
