# Copyright (C) 2022 Nippon Telegraph and Telephone Corporation
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

_LCCN_SUBSCRIPTION_ID = 'subscription_id'

_MIXED_CASE_FIELDS = ['filter', 'callbackUri']

_FORMATTERS = {
    'filter': tacker_osc_utils.FormatComplexDataColumn,
    '_links': tacker_osc_utils.FormatComplexDataColumn
}


def _get_columns(lccn_subsc_obj):

    column_map = {
        'id': 'ID',
        'filter': 'Filter',
        'callbackUri': 'Callback URI',
        '_links': 'Links'
    }

    return sdk_utils.get_osc_show_columns_for_sdk_resource(lccn_subsc_obj,
                                                           column_map)


class CreateLccnSubscription(command.ShowOne):
    _description = _("Create a new Lccn Subscription")

    def get_parser(self, prog_name):
        parser = super(CreateLccnSubscription, self).get_parser(prog_name)
        parser.add_argument(
            'create_request_file',
            metavar="<param-file>",
            help=_('Specify create request parameters in a json file.'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        subsc = client.create_lccn_subscription(
            tacker_osc_utils.jsonfile2body(parsed_args.create_request_file))
        display_columns, columns = _get_columns(subsc)
        data = utils.get_item_properties(sdk_utils.DictModel(subsc),
                                         columns, formatters=_FORMATTERS,
                                         mixed_case_fields=_MIXED_CASE_FIELDS)
        return (display_columns, data)


class DeleteLccnSubscription(command.Command):
    _description = _("Delete Lccn Subscription(s)")

    def get_parser(self, prog_name):
        parser = super(DeleteLccnSubscription, self).get_parser(prog_name)
        parser.add_argument(
            _LCCN_SUBSCRIPTION_ID,
            metavar="<subscription-id>",
            nargs="+",
            help=_("Lccn Subscription ID(s) to delete"))
        return parser

    def take_action(self, parsed_args):
        error_count = 0
        client = self.app.client_manager.tackerclient
        lccn_subscriptions = parsed_args.subscription_id
        for lccn_subscription in lccn_subscriptions:
            try:
                client.delete_lccn_subscription(lccn_subscription)
            except Exception as e:
                error_count += 1
                LOG.error(_("Failed to delete Lccn Subscription with "
                            "ID '%(subsc)s': %(e)s"),
                          {'subsc': lccn_subscription, 'e': e})

        total = len(lccn_subscriptions)
        if (error_count > 0):
            msg = (_("Failed to delete %(error_count)s of %(total)s "
                     "Lccn Subscriptions.") % {'error_count': error_count,
                                               'total': total})
            raise exceptions.CommandError(message=msg)
        else:
            if total > 1:
                print(_('All specified Lccn Subscriptions are deleted '
                        'successfully'))
            else:
                print(_("Lccn Subscription '%s' is deleted "
                        "successfully") % lccn_subscriptions[0])


class ListLccnSubscription(command.Lister):
    _description = _("List Lccn Subscriptions")

    def get_parser(self, program_name):
        parser = super(ListLccnSubscription, self).get_parser(program_name)
        parser.add_argument(
            "--filter",
            metavar="<filter>",
            help=_("Attribute-based-filtering parameters"),
        )
        return parser

    def get_attributes(self, exclude=None):
        fields = [
            {
                "key": "id",
                "value": "ID"
            },
            {
                "key": "callbackUri",
                "value": "Callback URI"
            }
        ]

        attributes = []

        for field in fields:
            attributes.extend([(field['key'], field['value'],
                              tacker_osc_utils.LIST_BOTH)])
        return tuple(attributes)

    def take_action(self, parsed_args):
        params = {}

        if parsed_args.filter:
            params['filter'] = parsed_args.filter

        client = self.app.client_manager.tackerclient
        subscriptions = client.list_lccn_subscriptions(**params)
        headers, columns = tacker_osc_utils.get_column_definitions(
            self.get_attributes(), long_listing=True)

        dictionary_properties = (utils.get_dict_properties(
            s, columns, mixed_case_fields=_MIXED_CASE_FIELDS)
            for s in subscriptions
        )

        return (headers, dictionary_properties)


class ShowLccnSubscription(command.ShowOne):
    _description = _("Display Lccn Subscription details")

    def get_parser(self, program_name):
        parser = super(ShowLccnSubscription, self).get_parser(program_name)
        parser.add_argument(
            _LCCN_SUBSCRIPTION_ID,
            metavar="<subscription-id>",
            help=_('Lccn Subscription ID to display'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj = client.show_lccn_subscription(parsed_args.subscription_id)
        display_columns, columns = _get_columns(obj)
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj),
            columns, formatters=_FORMATTERS,
            mixed_case_fields=_MIXED_CASE_FIELDS)
        return (display_columns, data)
