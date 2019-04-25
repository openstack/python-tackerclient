# Copyright (C) 2019 NTT DATA
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

from osc_lib.cli import parseractions
from osc_lib.command import command
from osc_lib import utils

from tackerclient.i18n import _
from tackerclient.osc import sdk_utils

LOG = logging.getLogger(__name__)

_mixed_case_fields = ('onboardingState', 'operationalState',
                      'usageState', 'userDefinedData')


def _get_columns(item):
    column_map = {
        '_links': 'Links',
        'onboardingState': 'Onboarding State',
        'operationalState': 'Operational State',
        'usageState': 'Usage State',
        'userDefinedData': 'User Defined Data',
        'id': 'ID'
    }
    return sdk_utils.get_osc_show_columns_for_sdk_resource(item, column_map)


class CreateVnfPackage(command.ShowOne):
    _description = _("Create a new VNF Package")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(CreateVnfPackage, self).get_parser(prog_name)
        parser.add_argument(
            '--user-data',
            metavar='<key=value>',
            action=parseractions.KeyValueAction,
            help=_('User defined data for the VNF package '
                   '(repeat option to set multiple user defined data)'),
        )
        return parser

    def args2body(self, parsed_args):
        body = {}
        if parsed_args.user_data:
            body["userDefinedData"] = parsed_args.user_data
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vnf_package = client.create_vnf_package(self.args2body(parsed_args))
        display_columns, columns = _get_columns(vnf_package)
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnf_package),
            columns, mixed_case_fields=_mixed_case_fields)
        return (display_columns, data)
